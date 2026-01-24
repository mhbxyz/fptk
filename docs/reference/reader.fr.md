# Reader

Le module `fptk.adt.reader` propose la monade `Reader`, principalement utilisée pour l'injection de dépendances. Elle permet de concevoir des fonctions dépendant d'un environnement global (configuration, services, contexte) sans avoir à transmettre explicitement cet environnement lors de chaque appel de fonction.

## Concept : La Monade Reader

La monade Reader modélise des calculs s'exécutant au sein d'un environnement partagé en lecture seule. Au lieu de polluer vos signatures de fonctions avec des paramètres de configuration, Reader assure la propagation automatique de cet environnement à travers vos calculs.

Voyez-la comme : **une fonction en attente de son environnement.**

```python
Reader[R, A]  ≈  R -> A
```

Ainsi, un `Reader[Config, User]` est un calcul qui, une fois muni d'une `Config`, produira un objet `User`.

### Le problème : la « propagation manuelle » des dépendances

```python
def obtenir_utilisateur(db: Database, cache: Cache, id: int) -> User:
    cached = cache.get(id)
    if cached:
        return cached
    user = db.query(id)
    cache.set(id, user)
    return user

def obtenir_publications(db: Database, cache: Cache, user_id: int) -> list[Post]:
    user = obtenir_utilisateur(db, cache, user_id)  # Transmission obligatoire
    return db.query_posts(user.id)

def generer_tableau_bord(db: Database, cache: Cache, user_id: int) -> Dashboard:
    user = obtenir_utilisateur(db, cache, user_id)  # Encore une transmission...
    posts = obtenir_publications(db, cache, user_id)  # Et encore une !
    return Dashboard(user, posts)
```

Chaque fonction doit accepter et retransmettre les dépendances `db` et `cache`. C'est une approche verbeuse, répétitive et propice aux erreurs d'inattention.

### La solution avec `Reader`

```python
from fptk.adt.reader import Reader, ask

@dataclass
class Env:
    db: Database
    cache: Cache

def obtenir_utilisateur(id: int) -> Reader[Env, User]:
    def run(env: Env) -> User:
        cached = env.cache.get(id)
        if cached:
            return cached
        user = env.db.query(id)
        env.cache.set(id, user)
        return user
    return Reader(run)

def obtenir_publications(user_id: int) -> Reader[Env, list[Post]]:
    return obtenir_utilisateur(user_id).bind(
        lambda user: ask().map(lambda env: env.db.query_posts(user.id))
    )

def generer_tableau_bord(user_id: int) -> Reader[Env, Dashboard]:
    return (
        obtenir_utilisateur(user_id)
        .bind(lambda user:
            obtenir_publications(user_id).map(lambda posts:
                Dashboard(user, posts)
            )
        )
    )

# Injection finale des dépendances réelles
env = Env(db=real_db, cache=real_cache)
tableau = generer_tableau_bord(42).run(env)
```

Les dépendances ne sont injectées qu'une seule fois, au point d'entrée de l'application. Les fonctions s'assemblent sans jamais avoir à manipuler explicitement l'objet `env`.

## API

### Types

| Type | Description |
| :--- | :--- |
| `Reader[R, A]` | Un calcul exigeant un environnement de type `R` pour produire un résultat de type `A`. |

### Constructeurs

```python
from fptk.adt.reader import Reader

# Création depuis une fonction
reader = Reader(lambda env: env.config["timeout"])
```

### Méthodes principales

| Méthode | Signature | Description |
| :--- | :--- | :--- |
| `map(f)` | `(A -> B) -> Reader[R, B]` | Transforme le résultat final du calcul. |
| `bind(f)` | `(A -> Reader[R, B]) -> Reader[R, B]` | Enchaîne deux calculs dépendant du même environnement. |
| `run(env)` | `(R) -> A` | Exécute effectivement le calcul avec l'environnement fourni. |

### Fonctions utilitaires

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `ask()` | `() -> Reader[R, R]` | Permet d'extraire l'environnement complet au sein d'un calcul. |
| `local(f, reader)` | `(R -> R, Reader[R, A]) -> Reader[R, A]` | Exécute un calcul dans une variante modifiée de l'environnement. |

## Fonctionnement technique

### Structure de données

`Reader` encapsule simplement une fonction prenant un environnement et renvoyant une valeur :

```python
@dataclass(frozen=True, slots=True)
class Reader[R, A]:
    run_reader: Callable[[R], A]

    def run(self, env: R) -> A:
        return self.run_reader(env)
```

### La Monade : `bind`

La méthode `bind` permet de séquencer des calculs partageant le même environnement :

```python
def bind(self, f):
    # Le même 'env' est transmis aux deux parties du calcul
    return Reader(lambda env: f(self.run_reader(env)).run_reader(env))
```

### `local` : modifier temporairement l'environnement

`local` est particulièrement utile pour modifier la portée d'un calcul sans altérer l'environnement global :

```python
# Exécute un calcul avec un timeout augmenté spécifiquement pour cet appel
local(lambda env: env._replace(timeout=30), mon_reader)
```

## Exemples d'utilisation

### Accès simplifié à la configuration

```python
@dataclass
class Config:
    db_url: str
    timeout: int

def obtenir_timeout() -> Reader[Config, int]:
    return ask().map(lambda c: c.timeout)

def chaine_connexion() -> Reader[Config, str]:
    return ask().map(lambda c: f"{c.db_url}?timeout={c.timeout}")

# Exécution
config = Config(db_url="postgres://localhost", timeout=30)
conn = chaine_connexion().run(config)
```

### Gestion des services et tests

`Reader` facilite grandement le remplacement de services réels par des mocks lors des tests :

```python
# En production
prod_services = Services(user_repo=PostgresRepo(), logger=CloudLogger())
resultat = mon_workflow().run(prod_services)

# En test
test_services = Services(user_repo=InMemoryRepo(), logger=NullLogger())
resultat = mon_workflow().run(test_services)
```

## Quand utiliser Reader ?

**Privilégiez Reader lorsque :**

-   Plusieurs fonctions ont besoin d'accéder aux mêmes dépendances (services, config).
-   Vous visez un code hautement testable grâce à l'injection de dépendances.
-   Vous construisez une bibliothèque ou un framework dont le comportement doit être configurable.
-   Vous souhaitez dissocier la définition de la logique métier (« quoi faire ») de ses ressources d'exécution (« avec quoi »).

**Évitez Reader lorsque :**

-   Seule une ou deux fonctions isolées ont besoin de la dépendance.
-   La dépendance est une constante véritablement globale qui ne change jamais.
-   La performance est ultra-critique (Reader ajoute une légère couche d'appels de fonctions).

## Voir aussi

-   [`State`](state.md) — Lorsque vous devez non seulement lire, mais aussi modifier un état.
-   [`Result`](result.md) — Pour combiner l'injection de dépendances avec des calculs faillibles.
-   [Effets de bord](../guide/side-effects.md) — Pour comprendre comment structurer une application propre.