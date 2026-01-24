# Les Effets de Bord à la Périphérie

La programmation fonctionnelle met l'accent sur la pureté : des fonctions prévisibles, testables et composables. Les effets de bord — opérations comme les E/S, les mutations ou les interactions externes — compliquent cela en introduisant de l'imprévisibilité et des dépendances.

Le principe de « garder les effets de bord à la périphérie » signifie structurer votre code de manière à ce que la logique métier centrale reste pure, avec les effets de bord gérés uniquement aux frontières de votre application.

## Pourquoi Garder les Effets de Bord à la Périphérie ?

- **Testabilité** : Les fonctions pures sont faciles à tester unitairement sans mocks ni configuration
- **Composabilité** : Les fonctions pures se combinent de manière prévisible ; les effets de bord non
- **Raisonnement** : Le code pur est plus facile à comprendre et à déboguer
- **Réutilisabilité** : La logique pure peut être réutilisée dans différents contextes

Sans ce principe, les effets de bord se répandent dans votre base de code, rendant difficile le raisonnement et la maintenance.

## Noyau Pur, Périphérie Impure

Structurez votre application ainsi :

1. **Noyau Pur** : La logique métier qui prend des entrées et produit des sorties sans effets de bord. Utilisez les ADTs comme `Result`, `Reader`, `State` et `Writer` pour modéliser les calculs de manière pure.
2. **Périphérie Impure** : Des couches minces qui gèrent les véritables effets de bord (lecture de fichiers, appels réseau, mutations), puis alimentent des entrées pures ou consomment des sorties pures.

La périphérie « interprète » les calculs purs dans le monde réel.

## Superposition avec Result

`Result[T, E]` modélise le succès/l'échec sans exceptions. Le superposer avec d'autres ADTs vous permet de gérer les erreurs tout en gardant les autres préoccupations (dépendances, état, journalisation) pures.

### Result + Reader : Injection de Dépendances avec Gestion d'Erreurs

`Reader[R, A]` fait passer un environnement en lecture seule (par exemple, la configuration) à travers les calculs. Combinez avec `Result` pour les calculs faillibles qui nécessitent une configuration.

```python
from dataclasses import dataclass
from fptk.adt.reader import Reader, ask
from fptk.adt.result import Ok, Err, Result

@dataclass
class Config:
    api_url: str
    timeout: int

def fetch_user(user_id: int) -> Reader[Config, Result[dict, str]]:
    """Pure computation: describe fetching user data."""
    def run(config: Config) -> Result[dict, str]:
        if user_id <= 0:
            return Err("Invalid user ID")
        # In pure core, we just describe what to do
        return Ok({"id": user_id, "url": config.api_url})
    return Reader(run)

def process_user(user_id: int) -> Reader[Config, Result[str, str]]:
    """Chain with error handling."""
    return fetch_user(user_id).map(
        lambda result: result.map(lambda user: f"Processed user {user['id']}")
    )

# Pure core: describe the workflow
config = Config(api_url="https://api.example.com", timeout=30)

# Edge: run with real config
result = process_user(1).run(config)
# Ok("Processed user 1")

result = process_user(-1).run(config)
# Err("Invalid user ID")
```

### Result + State : Calculs avec État et Gestion d'Erreurs

`State[S, A]` modélise les transitions d'état pures. Superposez avec `Result` pour les workflows avec état qui peuvent échouer.

```python
from fptk.adt.state import State, get, modify
from fptk.adt.result import Ok, Err, Result

def withdraw(amount: int) -> State[int, Result[int, str]]:
    """Pure state update with validation."""
    def run(balance: int) -> tuple[Result[int, str], int]:
        if amount > balance:
            return Err("Insufficient funds"), balance
        new_balance = balance - amount
        return Ok(new_balance), new_balance
    return State(run)

def transfer(amount: int) -> State[int, Result[str, str]]:
    """Chain stateful operations."""
    return withdraw(amount).map(
        lambda result: result.map(lambda bal: f"New balance: {bal}")
    )

# Pure core: describe the transfer
initial_balance = 100

# Edge: run and get final state
result, final_balance = transfer(30).run(initial_balance)
# result = Ok("New balance: 70"), final_balance = 70

result, final_balance = transfer(150).run(initial_balance)
# result = Err("Insufficient funds"), final_balance = 100
```

### Result + Writer : Calculs Journalisés avec Gestion d'Erreurs

`Writer[W, A]` accumule des logs aux côtés des valeurs. Superposez avec `Result` pour les calculs qui journalisent et peuvent échouer.

```python
from fptk.adt.writer import Writer, tell, monoid_list
from fptk.adt.result import Ok, Err, Result

def process_data(data: str) -> Writer[list[str], Result[int, str]]:
    """Pure computation with logging."""
    if not data:
        return Writer((Err("Empty data"), ["Error: empty input"]))

    return (
        tell(["Starting processing"])
        .bind(lambda _: tell([f"Processing {len(data)} chars"]))
        .map(lambda _: Ok(len(data)))
    )

# Edge: run and handle side effects
result, logs = process_data("hello world").run()
# result = Ok(11)
# logs = ["Starting processing", "Processing 11 chars"]

result, logs = process_data("").run()
# result = Err("Empty data")
# logs = ["Error: empty input"]

# Impure edge: write logs to file
def persist_logs(logs: list[str]) -> None:
    with open("app.log", "a") as f:
        for log in logs:
            f.write(log + "\n")
```

## Bonnes Pratiques

| Pratique | Description |
|----------|-------------|
| **Périphérie Mince** | Gardez le code impur minimal ; déléguez aux fonctions pures |
| **Propagation des Erreurs** | Utilisez `Result` pour faire remonter les erreurs jusqu'à la périphérie pour traitement |
| **Tests** | Testez facilement les noyaux purs ; mockez la périphérie uniquement si nécessaire |
| **Composition** | Construisez des workflows complexes en composant des fonctions pures plus simples |

## Exemple : Workflow Complet

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.adt.reader import Reader, ask

@dataclass
class AppConfig:
    db_url: str
    api_key: str

# Pure core: describe business logic
def validate_user(data: dict) -> Result[dict, str]:
    if not data.get("email"):
        return Err("Email required")
    return Ok(data)

def create_user_workflow(data: dict) -> Reader[AppConfig, Result[dict, str]]:
    """Pure workflow: validation -> save -> notify"""
    return ask().map(lambda config:
        validate_user(data)
        .map(lambda user: {**user, "db": config.db_url})
    )

# Impure edge: run with real config and perform I/O
def run_create_user(data: dict) -> Result[dict, str]:
    config = AppConfig(db_url="postgres://...", api_key="secret")
    result = create_user_workflow(data).run(config)

    # Handle side effects based on result
    if result.is_ok():
        user = result.unwrap()
        save_to_database(user)  # Impure
        send_email(user)        # Impure

    return result
```

En superposant `Result` avec d'autres ADTs et en gardant les effets de bord à la périphérie, vous construisez des applications robustes et maintenables qui sont faciles à comprendre et à tester.
