# Outils asynchrones (Async)

Le module `fptk.async_tools` propose des utilitaires pour orchestrer harmonieusement les opérations asynchrones (`async`) avec les types `Result`.

## Concept : Allier Async et Result

Dans un environnement asynchrone, les opérations renvoient fréquemment des types `Result` pour signaler leurs succès ou leurs échecs. Vous êtes ainsi souvent amené à :

1.  Lancer plusieurs tâches asynchrones en parallèle.
2.  Regrouper leurs issues respectives dans un unique `Result` global.
3.  Traiter les erreurs de façon structurée (arrêt immédiat ou accumulation).

```python
# Plusieurs opérations asynchrones susceptibles d'échouer
users = await gather_results([
    fetch_user(1),  # async -> Result[User, str]
    fetch_user(2),
    fetch_user(3),
])
# users: Result[list[User], str]
```

Cette approche est essentielle pour garantir :

-   **Une exécution concurrente** : optimisez vos performances en parallélisant les E/S.
-   **Une gestion d'erreurs unifiée** : faites converger naturellement les modèles `async` et `Result`.
-   **Une sémantique claire** : choisissez explicitement entre un arrêt au premier échec (fail-fast) ou la collecte de toutes les erreurs.

## API

### Fonctions

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `async_pipe(x, *fns)` | `async (T, *Callables) -> U` | Fait circuler une valeur à travers une suite de fonctions synchrones ou asynchrones. |
| `gather_results(tasks)` | `async (Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], E]` | Collecte les résultats en s'arrêtant à la première erreur rencontrée (fail-fast). |
| `gather_results_accumulate(tasks)` | `async (Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], list[E]]` | Collecte tous les résultats et l'ensemble des erreurs rencontrées. |

## Fonctionnement technique

### `async_pipe`

Cette fonction fait transiter une valeur à travers une séquence de fonctions. Elle détecte et attend (`await`) automatiquement toute valeur de retour étant un « awaitable » :

```python
async def async_pipe(x, *funcs):
    for f in funcs:
        x = f(x)
        if inspect.isawaitable(x):
            x = await x
    return x
```

Elle permet ainsi de mélanger toute liberté des fonctions synchrones et asynchrones au sein d'un même pipeline.

### `gather_results`

Elle lance toutes les tâches de front et renvoie soit la première erreur survenue, soit la liste complète des succès :

```python
async def gather_results(tasks):
    results = await asyncio.gather(*tasks)

    values = []
    first_err = None

    for r in results:
        if isinstance(r, Ok):
            values.append(r.value)
        elif first_err is None and isinstance(r, Err):
            first_err = r.error

    if first_err is not None:
        return Err(first_err)
    return Ok(values)
```

**Note importante** : même en cas d'erreur, toutes les tâches lancées vont jusqu'à leur terme (aucune annulation n'est déclenchée par la première erreur).

### `gather_results_accumulate`

Similaire à `gather_results`, cette variante ne s'arrête jamais en cours de route et collecte systématiquement toutes les erreurs :

```python
async def gather_results_accumulate(tasks):
    results = await asyncio.gather(*tasks)

    values = []
    errors = []

    for r in results:
        if isinstance(r, Ok):
            values.append(r.value)
        elif isinstance(r, Err):
            errors.append(r.error)

    if errors:
        return Err(errors)
    return Ok(values)
```

## Exemples d'utilisation

### Récupération concurrente simple

```python
from fptk.async_tools import gather_results
from fptk.adt.result import Ok, Err

async def fetch_user(id: int) -> Result[User, str]:
    try:
        user = await db.async_get(id)
        return Ok(user) if user else Err(f"Utilisateur {id} introuvable")
    except Exception as e:
        return Err(f"Erreur de base de données : {e}")

async def fetch_all_users(ids: list[int]) -> Result[list[User], str]:
    tasks = [fetch_user(id) for id in ids]
    return await gather_results(tasks)

# Utilisation
result = await fetch_all_users([1, 2, 3])
result.match(
    ok=lambda users: print(f"{len(users)} utilisateurs récupérés"),
    err=lambda e: print(f"Échec : {e}")
)
```

### Accumulation de toutes les erreurs

```python
from fptk.async_tools import gather_results_accumulate

async def validate_user_async(id: int) -> Result[User, str]:
    user = await fetch_user(id)
    if not user:
        return Err(f"Utilisateur {id} introuvable")
    if not user.email:
        return Err(f"L'utilisateur {id} n'a pas d'email")
    return Ok(user)

async def validate_batch(ids: list[int]) -> Result[list[User], list[str]]:
    tasks = [validate_user_async(id) for id in ids]
    return await gather_results_accumulate(tasks)

# Récupération de l'ensemble des erreurs en une fois
result = await validate_batch([1, 2, 3, 4, 5])
result.match(
    ok=lambda users: print(f"Tous valides : {len(users)} utilisateurs"),
    err=lambda errors: print(f"Erreurs détectées : {errors}")
)
```

### Pipeline asynchrone mixte

```python
from fptk.async_tools import async_pipe

async def fetch_user(id: int) -> User:
    return await db.get_user(id)

def validate(user: User) -> User:
    if not user.active:
        raise ValueError("Utilisateur inactif")
    return user

async def enrich_with_posts(user: User) -> User:
    posts = await db.get_posts(user.id)
    return user.with_posts(posts)

def format_response(user: User) -> dict:
    return {"user": user.to_dict()}

# Combinaison fluide de fonctions sync et async
response = await async_pipe(
    user_id,
    fetch_user,        # async
    validate,          # sync
    enrich_with_posts, # async
    format_response    # sync
)
```

### Traitement par lots avec contrôle de concurrence

```python
from fptk.async_tools import gather_results
from fptk.iter.lazy import chunk

async def process_item(item: Item) -> Result[Processed, str]:
    try:
        result = await external_api.process(item)
        return Ok(result)
    except Exception as e:
        return Err(f"Échec du traitement pour {item.id} : {e}")

async def process_batch(items: list[Item], batch_size: int = 10):
    """Traite les éléments par lots pour limiter la charge."""
    all_results = []

    for batch in chunk(items, batch_size):
        tasks = [process_item(item) for item in batch]
        batch_result = await gather_results(tasks)

        if batch_result.is_err():
            return batch_result  # Arrêt immédiat en cas d'erreur sur un lot

        all_results.extend(batch_result.unwrap())

    return Ok(all_results)
```

## Comparaison : gather_results vs gather_results_accumulate

| Aspect | `gather_results` | `gather_results_accumulate` |
| :--- | :--- | :--- |
| **En cas d'erreur** | S'arrête logiquement (mais les tâches en cours se terminent). | Collecte toutes les erreurs rencontrées. |
| **Type de retour** | `Result[list[T], E]` | `Result[list[T], list[E]]` |
| **Cas d'usage** | Vous n'avez besoin que du signal de premier échec. | Vous exigez un rapport exhaustif des anomalies. |

## Quand utiliser ces outils ?

**Privilégiez `gather_results` lorsque :**

-   Vous lancez des opérations asynchrones indépendantes.
-   Un seul échec suffit à invalider l'ensemble du processus.
-   Vous récupérez plusieurs ressources dont la totalité est requise.

**Privilégiez `gather_results_accumulate` lorsque :**

-   Vous avez besoin d'une visibilité complète sur tous les échecs possibles.
-   Vous effectuez des validations de masse en parallèle.
-   Vous construisez des rapports d'erreurs détaillés.

**Privilégiez `async_pipe` lorsque :**

-   Vous concevez des pipelines de transformation asynchrones.
-   Votre logique mêle étroitement fonctions synchrones et asynchrones.
-   Vous visez un flux de données linéaire, propre et lisible.

## Voir aussi

-   [`Result`](result.md) — Le type `Result` fondamental.
-   [`traverse_result_async`](traverse.md) — Pour un parcours asynchrone séquentiel.
-   [Développement d'API](../recipes/api-development.md) — L'asynchrone dans les contextes web.
-   [Traitement de données](../recipes/data-processing.md) — Le traitement par lots asynchrone.