# Outils Async

`fptk.async_tools` fournit des utilitaires pour travailler avec les operations async et les types `Result` ensemble.

## Concept : Async et Result

Lorsque vous travaillez avec du code async, les operations retournent souvent des types `Result` pour gerer les erreurs. Vous avez frequemment besoin de :

1. Executer plusieurs operations async en parallele
2. Collecter leurs resultats dans un seul `Result`
3. Gerer les erreurs de maniere appropriee (fail-fast ou accumulation)

```python
# Multiple async operations that might fail
users = await gather_results([
    fetch_user(1),  # async -> Result[User, str]
    fetch_user(2),
    fetch_user(3),
])
# users: Result[list[User], str]
```

Cela est important car :

- **Execution concurrente** : Executez les operations I/O en parallele
- **Gestion d'erreurs unifiee** : Combinez les patterns async et Result
- **Semantique coherente** : Choisissez fail-fast ou accumulation d'erreurs

## API

### Fonctions

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `async_pipe(x, *fns)` | `async (T, *Callables) -> U` | Passe une valeur a travers des fonctions async/sync |
| `gather_results(tasks)` | `async (Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], E]` | Collecte les resultats, fail-fast |
| `gather_results_accumulate(tasks)` | `async (Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], list[E]]` | Collecte les resultats, accumule les erreurs |

## Fonctionnement

### `async_pipe`

Passe une valeur a travers une sequence de fonctions, en attendant celles qui retournent des awaitables :

```python
async def async_pipe(x, *funcs):
    for f in funcs:
        x = f(x)
        if inspect.isawaitable(x):
            x = await x
    return x
```

Permet de melanger des fonctions sync et async dans le meme pipeline.

### `gather_results`

Execute toutes les taches en parallele, retourne la premiere erreur ou tous les succes :

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

**Note** : Toutes les taches s'executent jusqu'a la fin (pas d'annulation a la premiere erreur).

### `gather_results_accumulate`

Comme `gather_results`, mais collecte toutes les erreurs :

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

## Exemples

### Recuperation concurrente basique

```python
from fptk.async_tools import gather_results
from fptk.adt.result import Ok, Err

async def fetch_user(id: int) -> Result[User, str]:
    try:
        user = await db.async_get(id)
        return Ok(user) if user else Err(f"User {id} not found")
    except Exception as e:
        return Err(f"Database error: {e}")

async def fetch_all_users(ids: list[int]) -> Result[list[User], str]:
    tasks = [fetch_user(id) for id in ids]
    return await gather_results(tasks)

# Usage
result = await fetch_all_users([1, 2, 3])
result.match(
    ok=lambda users: print(f"Got {len(users)} users"),
    err=lambda e: print(f"Failed: {e}")
)
```

### Accumuler toutes les erreurs

```python
from fptk.async_tools import gather_results_accumulate

async def validate_user_async(id: int) -> Result[User, str]:
    user = await fetch_user(id)
    if not user:
        return Err(f"User {id} not found")
    if not user.email:
        return Err(f"User {id} has no email")
    return Ok(user)

async def validate_batch(ids: list[int]) -> Result[list[User], list[str]]:
    tasks = [validate_user_async(id) for id in ids]
    return await gather_results_accumulate(tasks)

# Get all errors at once
result = await validate_batch([1, 2, 3, 4, 5])
result.match(
    ok=lambda users: print(f"All valid: {len(users)} users"),
    err=lambda errors: print(f"Errors: {errors}")
)
```

### Pipeline async

```python
from fptk.async_tools import async_pipe

async def fetch_user(id: int) -> User:
    return await db.get_user(id)

def validate(user: User) -> User:
    if not user.active:
        raise ValueError("User inactive")
    return user

async def enrich_with_posts(user: User) -> User:
    posts = await db.get_posts(user.id)
    return user.with_posts(posts)

def format_response(user: User) -> dict:
    return {"user": user.to_dict()}

# Mix sync and async seamlessly
response = await async_pipe(
    user_id,
    fetch_user,        # async
    validate,          # sync
    enrich_with_posts, # async
    format_response    # sync
)
```

### Appels API paralleles

```python
from fptk.async_tools import gather_results
import aiohttp

async def fetch_url(url: str) -> Result[dict, str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return Ok(await response.json())
                return Err(f"HTTP {response.status} for {url}")
    except Exception as e:
        return Err(f"Request failed: {e}")

async def fetch_all_apis(urls: list[str]) -> Result[list[dict], str]:
    tasks = [fetch_url(url) for url in urls]
    return await gather_results(tasks)

# Fetch multiple APIs concurrently
data = await fetch_all_apis([
    "https://api.example.com/users",
    "https://api.example.com/posts",
    "https://api.example.com/comments",
])
```

### Traitement par lots avec Results

```python
from fptk.async_tools import gather_results
from fptk.iter.lazy import chunk

async def process_item(item: Item) -> Result[Processed, str]:
    try:
        result = await external_api.process(item)
        return Ok(result)
    except Exception as e:
        return Err(f"Failed to process {item.id}: {e}")

async def process_batch(items: list[Item], batch_size: int = 10):
    """Process items in batches with concurrency control."""
    all_results = []

    for batch in chunk(items, batch_size):
        tasks = [process_item(item) for item in batch]
        batch_result = await gather_results(tasks)

        if batch_result.is_err():
            return batch_result  # Fail-fast on batch error

        all_results.extend(batch_result.unwrap())

    return Ok(all_results)
```

### Combinaison avec Traverse

```python
from fptk.adt.traverse import traverse_result_async
from fptk.async_tools import gather_results

# Sequential async (one at a time)
result = await traverse_result_async(ids, fetch_user)

# Parallel async (all at once)
result = await gather_results([fetch_user(id) for id in ids])

# Choose based on:
# - Rate limits: use sequential
# - Performance: use parallel
# - Resource constraints: use batched parallel
```

### Recuperation d'erreurs

```python
from fptk.async_tools import gather_results_accumulate
from fptk.adt.result import Ok, Err

async def fetch_with_retry(id: int, retries: int = 3) -> Result[User, str]:
    for attempt in range(retries):
        result = await fetch_user(id)
        if result.is_ok():
            return result
        # Wait before retry
        await asyncio.sleep(2 ** attempt)
    return Err(f"Failed after {retries} retries for {id}")

async def fetch_best_effort(ids: list[int]):
    """Fetch all, log errors, return what succeeded."""
    result = await gather_results_accumulate(
        [fetch_with_retry(id) for id in ids]
    )

    return result.match(
        ok=lambda users: users,
        err=lambda errors: {
            "partial_results": [],  # Would need more complex handling
            "errors": errors
        }
    )
```

### Gestion du timeout

```python
from fptk.async_tools import gather_results

async def fetch_with_timeout(id: int, timeout: float = 5.0) -> Result[User, str]:
    try:
        user = await asyncio.wait_for(fetch_user_raw(id), timeout=timeout)
        return Ok(user)
    except asyncio.TimeoutError:
        return Err(f"Timeout fetching user {id}")
    except Exception as e:
        return Err(str(e))

async def fetch_all_with_timeout(ids: list[int]) -> Result[list[User], str]:
    return await gather_results(
        [fetch_with_timeout(id) for id in ids]
    )
```

## Comparaison : gather_results vs gather_results_accumulate

| Fonction | A la premiere erreur | Type de retour | A utiliser quand |
|----------|---------------|-------------|----------|
| `gather_results` | S'arrete (mais les taches continuent) | `Result[list[T], E]` | Vous n'avez besoin que de la premiere erreur |
| `gather_results_accumulate` | Collecte toutes | `Result[list[T], list[E]]` | Vous voulez toutes les erreurs |

```python
# Fail-fast semantics
await gather_results([ok1, err1, err2, ok2])
# Err(err1.error) - only first error

# Accumulate semantics
await gather_results_accumulate([ok1, err1, err2, ok2])
# Err([err1.error, err2.error]) - all errors
```

## Quand utiliser les outils async

**Utilisez gather_results quand :**

- Vous executez des operations async independantes en parallele
- Vous voulez un comportement fail-fast
- Vous recuperez plusieurs ressources en parallele

**Utilisez gather_results_accumulate quand :**

- Vous avez besoin de voir toutes les erreurs
- Vous validez plusieurs elements en parallele
- Vous construisez des rapports d'erreurs complets

**Utilisez async_pipe quand :**

- Vous construisez des pipelines de transformation async
- Vous melangez des fonctions sync et async
- Vous voulez un flux de donnees lineaire et lisible

## Voir aussi

- [`Result`](result.md) - Le type Result sous-jacent
- [`traverse_result_async`](traverse.md) - Traversal async sequentiel
- [Recette developpement API](../recipes/api-development.md) - Async dans les APIs web
- [Recette traitement de donnees](../recipes/data-processing.md) - Traitement par lots async
