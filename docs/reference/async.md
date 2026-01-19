# Async Tools

`fptk.async_tools` provides utilities for working with async operations and `Result` types together.

## Concept: Async and Result

When working with async code, operations often return `Result` types to handle errors. You frequently need to:

1. Run multiple async operations concurrently
2. Collect their results into a single `Result`
3. Handle errors appropriately (fail-fast or accumulate)

```python
# Multiple async operations that might fail
users = await gather_results([
    fetch_user(1),  # async -> Result[User, str]
    fetch_user(2),
    fetch_user(3),
])
# users: Result[list[User], str]
```

This matters because:

- **Concurrent execution**: Run I/O operations in parallel
- **Unified error handling**: Combine async and Result patterns
- **Consistent semantics**: Choose fail-fast or error accumulation

## API

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `async_pipe(x, *fns)` | `async (T, *Callables) -> U` | Thread value through async/sync functions |
| `gather_results(tasks)` | `async (Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], E]` | Collect results, fail-fast |
| `gather_results_accumulate(tasks)` | `async (Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], list[E]]` | Collect results, accumulate errors |

## How It Works

### `async_pipe`

Threads a value through a sequence of functions, awaiting any that return awaitables:

```python
async def async_pipe(x, *funcs):
    for f in funcs:
        x = f(x)
        if inspect.isawaitable(x):
            x = await x
    return x
```

Allows mixing sync and async functions in the same pipeline.

### `gather_results`

Runs all tasks concurrently, returns first error or all successes:

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

**Note**: All tasks run to completion (no cancellation on first error).

### `gather_results_accumulate`

Like `gather_results`, but collects all errors:

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

## Examples

### Basic Concurrent Fetch

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

### Accumulating All Errors

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

### Async Pipeline

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

### Parallel API Calls

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

### Batch Processing with Results

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

### Combining with Traverse

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

### Error Recovery

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

### Timeout Handling

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

## Comparison: gather_results vs gather_results_accumulate

| Function | On First Error | Return Type | Use When |
|----------|---------------|-------------|----------|
| `gather_results` | Stops (but tasks still run) | `Result[list[T], E]` | You only need first error |
| `gather_results_accumulate` | Collects all | `Result[list[T], list[E]]` | You want all errors |

```python
# Fail-fast semantics
await gather_results([ok1, err1, err2, ok2])
# Err(err1.error) - only first error

# Accumulate semantics
await gather_results_accumulate([ok1, err1, err2, ok2])
# Err([err1.error, err2.error]) - all errors
```

## When to Use Async Tools

**Use gather_results when:**

- Running independent async operations concurrently
- You want fail-fast behavior
- Fetching multiple resources in parallel

**Use gather_results_accumulate when:**

- You need to see all errors
- Validating multiple items concurrently
- Building comprehensive error reports

**Use async_pipe when:**

- Building async transformation pipelines
- Mixing sync and async functions
- You want linear, readable data flow

## See Also

- [`Result`](result.md) — The underlying Result type
- [`traverse_result_async`](traverse.md) — Sequential async traversal
- [API Development Recipe](../recipes/api-development.md) — Async in web APIs
- [Data Processing Recipe](../recipes/data-processing.md) — Async batch processing
