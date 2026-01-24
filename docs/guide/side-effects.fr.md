# Les effets de bord à la périphérie

La programmation fonctionnelle met l'accent sur la pureté : des fonctions prévisibles, testables et composables. Les effets de bord — comme les entrées/sorties (E/S), les mutations ou les interactions externes — viennent complexifier ce modèle en introduisant de l'imprévisibilité et des dépendances.

Le principe consistant à « maintenir les effets de bord à la périphérie » vise à structurer votre code de sorte que la logique métier centrale reste pure, les effets de bord étant cantonnés aux frontières de votre application.

## Pourquoi maintenir les effets de bord à la périphérie ?

-   **Testabilité** : Les fonctions pures sont faciles à tester unitairement, sans mocks ni configurations complexes.
-   **Composabilité** : Les fonctions pures s'assemblent de manière prévisible, contrairement aux effets de bord.
-   **Clarté du raisonnement** : Un code pur est plus simple à appréhender et à déboguer.
-   **Réutilisabilité** : Une logique pure peut être réemployée sans difficulté dans différents contextes.

Sans ce principe, les effets de bord s'insinuent partout dans votre codebase, rendant sa compréhension et sa maintenance ardues.

## Noyau Pur, Périphérie Impure

Structurez votre application selon ce modèle :

1.  **Noyau Pur (Pure Core)** : La logique métier qui traite des entrées et produit des sorties sans effets de bord. Utilisez des ADT comme `Result`, `Reader`, `State` et `Writer` pour modéliser vos calculs de façon pure.
2.  **Périphérie Impure (Impure Edges)** : Des couches minces qui gèrent les véritables effets de bord (lecture de fichiers, appels réseau, mutations), puis alimentent le noyau en entrées pures ou en consomment les sorties.

La périphérie agit comme un « interprète » traduisant les calculs purs dans le monde réel.

## Superposition avec Result

`Result[T, E]` modélise le succès ou l'échec sans recourir aux exceptions. En le superposant avec d'autres ADT, vous gérez les erreurs tout en isolant d'autres préoccupations (dépendances, état, journalisation) de manière pure.

### Result + Reader : Injection de dépendances et gestion d'erreurs

`Reader[R, A]` fait circuler un environnement en lecture seule (comme une configuration) à travers vos calculs. Combiné avec `Result`, il permet de gérer des calculs faillibles nécessitant une configuration.

```python
from dataclasses import dataclass
from fptk.adt.reader import Reader, ask
from fptk.adt.result import Ok, Err, Result

@dataclass
class Config:
    api_url: str
    timeout: int

def fetch_user(user_id: int) -> Reader[Config, Result[dict, str]]:
    """Calcul pur : décrit la récupération des données utilisateur."""
    def run(config: Config) -> Result[dict, str]:
        if user_id <= 0:
            return Err("ID utilisateur invalide")
        # Dans le noyau pur, on se contente de décrire l'action
        return Ok({"id": user_id, "url": config.api_url})
    return Reader(run)

def process_user(user_id: int) -> Reader[Config, Result[str, str]]:
    """Chaînage avec gestion d'erreurs."""
    return fetch_user(user_id).map(
        lambda result: result.map(lambda user: f"Utilisateur {user['id']} traité")
    )

# Noyau pur : description du workflow
config = Config(api_url="https://api.example.com", timeout=30)

# Périphérie : exécution avec la configuration réelle
result = process_user(1).run(config)
# Ok("Utilisateur 1 traité")

result = process_user(-1).run(config)
# Err("ID utilisateur invalide")
```

### Result + State : Calculs avec état et gestion d'erreurs

`State[S, A]` modélise des transitions d'état pures. Superposez-le avec `Result` pour des workflows avec état susceptibles d'échouer.

```python
from fptk.adt.state import State, get, modify
from fptk.adt.result import Ok, Err, Result

def withdraw(amount: int) -> State[int, Result[int, str]]:
    """Mise à jour d'état pure avec validation."""
    def run(balance: int) -> tuple[Result[int, str], int]:
        if amount > balance:
            return Err("Fonds insuffisants"), balance
        new_balance = balance - amount
        return Ok(new_balance), new_balance
    return State(run)

def transfer(amount: int) -> State[int, Result[str, str]]:
    """Chaînage d'opérations avec état."""
    return withdraw(amount).map(
        lambda result: result.map(lambda bal: f"Nouveau solde : {bal}")
    )

# Noyau pur : description du transfert
initial_balance = 100

# Périphérie : exécution et récupération de l'état final
result, final_balance = transfer(30).run(initial_balance)
# result = Ok("Nouveau solde : 70"), final_balance = 70

result, final_balance = transfer(150).run(initial_balance)
# result = Err("Fonds insuffisants"), final_balance = 100
```

### Result + Writer : Calculs journalisés et gestion d'erreurs

`Writer[W, A]` accumule des journaux (logs) parallèlement aux valeurs produites. Superposez-le avec `Result` pour des calculs qui journalisent leur activité et peuvent échouer.

```python
from fptk.adt.writer import Writer, tell, monoid_list
from fptk.adt.result import Ok, Err, Result

def process_data(data: str) -> Writer[list[str], Result[int, str]]:
    """Calcul pur avec journalisation."""
    if not data:
        return Writer((Err("Données vides"), ["Erreur : entrée vide"]))

    return (
        tell(["Démarrage du traitement"])
        .bind(lambda _: tell([f"Traitement de {len(data)} caractères"]))
        .map(lambda _: Ok(len(data)))
    )

# Périphérie : exécution et gestion des effets de bord
result, logs = process_data("bonjour le monde").run()
# result = Ok(16)
# logs = ["Démarrage du traitement", "Traitement de 16 caractères"]

result, logs = process_data("").run()
# result = Err("Données vides")
# logs = ["Erreur : entrée vide"]

# Périphérie impure : écriture effective des journaux dans un fichier
def persist_logs(logs: list[str]) -> None:
    with open("app.log", "a") as f:
        for log in logs:
            f.write(log + "\n")
```

## Bonnes pratiques

| Pratique | Description |
| :--- | :--- |
| **Périphérie mince** | Limitez le code impur au strict nécessaire ; déléguez le reste aux fonctions pures. |
| **Propagation des erreurs** | Utilisez `Result` pour faire remonter les erreurs jusqu'à la périphérie pour traitement. |
| **Tests** | Testez prioritairement les noyaux purs ; n'utilisez des mocks en périphérie que si nécessaire. |
| **Composition** | Bâtissez des workflows complexes en assemblant des fonctions pures simples. |

## Exemple : Un workflow complet

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.adt.reader import Reader, ask

@dataclass
class AppConfig:
    db_url: str
    api_key: str

# Noyau pur : description de la logique métier
def validate_user(data: dict) -> Result[dict, str]:
    if not data.get("email"):
        return Err("Email requis")
    return Ok(data)

def create_user_workflow(data: dict) -> Reader[AppConfig, Result[dict, str]]:
    """Workflow pur : validation -> sauvegarde -> notification"""
    return ask().map(lambda config:
        validate_user(data)
        .map(lambda user: {**user, "db": config.db_url})
    )

# Périphérie impure : exécution avec configuration réelle et E/S
def run_create_user(data: dict) -> Result[dict, str]:
    config = AppConfig(db_url="postgres://...", api_key="secret")
    result = create_user_workflow(data).run(config)

    # Gestion des effets de bord selon le résultat
    if result.is_ok():
        user = result.unwrap()
        save_to_database(user)  # Impure
        send_email(user)        # Impure

    return result
```

En superposant `Result` avec d'autres ADT et en isolant les effets de bord à la périphérie, vous concevez des applications robustes, faciles à comprendre, à tester et à maintenir.