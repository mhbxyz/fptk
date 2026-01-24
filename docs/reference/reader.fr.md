# Reader

`fptk.adt.reader` fournit la monade `Reader` pour l'injection de dépendances. Elle vous permet d'écrire des fonctions qui dépendent d'un environnement (configuration, services, contexte) sans passer explicitement cet environnement à chaque appel de fonction.

## Concept : La monade Reader

La monade Reader représente des calculs qui dépendent d'un environnement partagé en lecture seule. Au lieu de passer la configuration ou les dépendances à travers chaque paramètre de fonction, Reader les propage automatiquement.

Considérez-la comme : **une fonction en attente de son environnement**.

```python
Reader[R, A]  ≈  R -> A
```

Un `Reader[Config, User]` est un calcul qui, étant donné une `Config`, produit un `User`.

### Le problème : La propagation des dépendances

```python
def get_user(db: Database, cache: Cache, id: int) -> User:
    cached = cache.get(id)
    if cached:
        return cached
    user = db.query(id)
    cache.set(id, user)
    return user

def get_user_posts(db: Database, cache: Cache, user_id: int) -> list[Post]:
    user = get_user(db, cache, user_id)  # Must pass db, cache
    return db.query_posts(user.id)

def get_dashboard(db: Database, cache: Cache, user_id: int) -> Dashboard:
    user = get_user(db, cache, user_id)  # Pass again
    posts = get_user_posts(db, cache, user_id)  # And again
    return Dashboard(user, posts)
```

Chaque fonction doit explicitement accepter et passer `db` et `cache`. C'est verbeux et source d'erreurs.

### La solution Reader

```python
from fptk.adt.reader import Reader, ask

@dataclass
class Env:
    db: Database
    cache: Cache

def get_user(id: int) -> Reader[Env, User]:
    def run(env: Env) -> User:
        cached = env.cache.get(id)
        if cached:
            return cached
        user = env.db.query(id)
        env.cache.set(id, user)
        return user
    return Reader(run)

def get_user_posts(user_id: int) -> Reader[Env, list[Post]]:
    return get_user(user_id).bind(
        lambda user: ask().map(lambda env: env.db.query_posts(user.id))
    )

def get_dashboard(user_id: int) -> Reader[Env, Dashboard]:
    return (
        get_user(user_id)
        .bind(lambda user:
            get_user_posts(user_id).map(lambda posts:
                Dashboard(user, posts)
            )
        )
    )

# Run with actual dependencies
env = Env(db=real_db, cache=real_cache)
dashboard = get_dashboard(42).run(env)
```

Les dépendances sont injectées une seule fois au niveau supérieur. Les fonctions se composent sans passer `env`.

## API

### Types

| Type | Description |
|------|-------------|
| `Reader[R, A]` | Calcul nécessitant l'environnement `R` pour produire `A` |

### Constructeur

```python
from fptk.adt.reader import Reader

# Create from a function
reader = Reader(lambda env: env.config["timeout"])
```

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `map(f)` | `(A -> B) -> Reader[R, B]` | Transforme le résultat |
| `bind(f)` | `(A -> Reader[R, B]) -> Reader[R, B]` | Chaîne des fonctions retournant un Reader |
| `run(env)` | `(R) -> A` | Exécute avec l'environnement |

### Fonctions

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `ask()` | `() -> Reader[R, R]` | Obtient l'environnement complet |
| `local(f, reader)` | `(R -> R, Reader[R, A]) -> Reader[R, A]` | Exécute avec un environnement modifié |

## Fonctionnement

### Structure de données

Reader encapsule une fonction de l'environnement vers une valeur :

```python
@dataclass(frozen=True, slots=True)
class Reader[R, A]:
    run_reader: Callable[[R], A]

    def run(self, env: R) -> A:
        return self.run_reader(env)
```

### Le Functor : `map`

`map` transforme le résultat tout en conservant la dépendance à l'environnement :

```python
def map(self, f):
    return Reader(lambda env: f(self.run_reader(env)))
```

### La Monade : `bind`

`bind` chaîne des calculs qui dépendent tous les deux de l'environnement :

```python
def bind(self, f):
    return Reader(lambda env: f(self.run_reader(env)).run_reader(env))
```

Point clé : le même `env` est passé au Reader original et au Reader retourné par `f`.

### `ask` : Accéder à l'environnement

`ask()` crée un Reader qui retourne simplement l'environnement :

```python
def ask():
    return Reader(lambda env: env)
```

Utilisez-le lorsque vous devez accéder à l'environnement au milieu d'une chaîne :

```python
ask().map(lambda env: env.config["database_url"])
```

### `local` : Modifier l'environnement temporairement

`local` exécute un Reader avec un environnement transformé :

```python
def local(f, reader):
    return Reader(lambda env: reader.run_reader(f(env)))
```

Utile pour les tests ou les surcharges localisées :

```python
# Run with increased timeout
local(lambda env: env._replace(timeout=30), my_reader)
```

## Exemples

### Accès à la configuration

```python
from fptk.adt.reader import Reader, ask
from dataclasses import dataclass

@dataclass
class Config:
    db_url: str
    timeout: int
    debug: bool

def get_timeout() -> Reader[Config, int]:
    return ask().map(lambda c: c.timeout)

def get_db_url() -> Reader[Config, str]:
    return ask().map(lambda c: c.db_url)

def connection_string() -> Reader[Config, str]:
    return (
        get_db_url()
        .bind(lambda url:
            get_timeout().map(lambda timeout:
                f"{url}?timeout={timeout}"
            )
        )
    )

# Run
config = Config(db_url="postgres://localhost", timeout=30, debug=True)
conn = connection_string().run(config)
# "postgres://localhost?timeout=30"
```

### Dépendances de services

```python
@dataclass
class Services:
    user_repo: UserRepository
    email_service: EmailService
    logger: Logger

def create_user(data: dict) -> Reader[Services, Result[User, str]]:
    def run(s: Services) -> Result[User, str]:
        user = User.from_dict(data)
        result = s.user_repo.save(user)
        if result.is_ok():
            s.email_service.send_welcome(user.email)
            s.logger.info(f"Created user {user.id}")
        return result
    return Reader(run)

def get_user_with_posts(id: int) -> Reader[Services, Option[UserWithPosts]]:
    return ask().map(lambda s:
        from_nullable(s.user_repo.find(id))
        .map(lambda user:
            UserWithPosts(user, s.post_repo.find_by_user(id))
        )
    )
```

### Tests avec un environnement simulé

```python
# Production
prod_services = Services(
    user_repo=PostgresUserRepo(),
    email_service=SendGridService(),
    logger=CloudLogger()
)
result = create_user(data).run(prod_services)

# Testing
test_services = Services(
    user_repo=InMemoryUserRepo(),
    email_service=MockEmailService(),
    logger=NullLogger()
)
result = create_user(data).run(test_services)
```

### Utiliser `local` pour des changements localisés

```python
def with_debug(reader: Reader[Config, A]) -> Reader[Config, A]:
    """Run a reader with debug mode enabled."""
    return local(lambda c: dataclasses.replace(c, debug=True), reader)

def process_request(req: Request) -> Reader[Config, Response]:
    computation = ...  # some Reader

    # Enable debug for certain requests
    if req.headers.get("X-Debug"):
        return with_debug(computation)
    return computation
```

### Combiner avec Result

```python
def fetch_user(id: int) -> Reader[Services, Result[User, str]]:
    return ask().map(lambda s:
        try_catch(s.user_repo.find)(id)
        .map_err(lambda e: f"Database error: {e}")
        .bind(lambda user:
            Ok(user) if user else Err(f"User {id} not found")
        )
    )

def fetch_user_posts(user_id: int) -> Reader[Services, Result[list[Post], str]]:
    return (
        fetch_user(user_id)
        .bind(lambda result:
            result.match(
                ok=lambda user: ask().map(lambda s:
                    Ok(s.post_repo.find_by_user(user.id))
                ),
                err=lambda e: Reader(lambda _: Err(e))
            )
        )
    )
```

## Quand utiliser Reader

**Utilisez Reader lorsque :**

- Vous avez des dépendances dont de nombreuses fonctions ont besoin
- Vous voulez du code testable avec des dépendances injectables
- Vous construisez un framework ou une bibliothèque avec un comportement configurable
- Vous voulez séparer "quoi faire" de "avec quoi le faire"

**N'utilisez pas Reader lorsque :**

- Vous n'avez qu'une ou deux fonctions qui ont besoin de la dépendance
- La dépendance est vraiment globale et ne change jamais
- Les performances sont critiques (Reader ajoute une surcharge d'appel de fonction)

## Reader vs autres patterns

| Pattern | Quand l'utiliser |
|---------|------------------|
| Reader | Injection de dépendances pure, pipelines composables |
| Variables globales | Jamais (en général) |
| Paramètres explicites | Peu de fonctions, dépendances simples |
| Classe avec self | Conception orientée objet |
| Framework d'injection de dépendances | Applications volumineuses avec des cycles de vie complexes |

Reader est particulièrement utile lorsque vous voulez les avantages de l'injection de dépendances tout en gardant votre code purement fonctionnel et composable.

## Voir aussi

- [`State`](state.md) — Lorsque vous devez à la fois lire et écrire l'état
- [`Result`](result.md) — Combiner avec Reader pour des calculs faillibles
- [Effets de bord](../guide/side-effects.md) — Coeurs purs avec effets aux frontières
