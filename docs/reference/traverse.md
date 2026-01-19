# Traverse

`fptk.adt.traverse` provides operations to work with collections of `Option` or `Result` values, turning them "inside out" while handling failures.

## Concept: Traverse and Sequence

When you have a list of computations that might fail, you often want to:

1. **Sequence**: Turn `list[Option[T]]` into `Option[list[T]]`
2. **Traverse**: Map a function over a list, then sequence the results

These operations "flip" the container structure:

```
list[Option[T]]  →  Option[list[T]]
list[Result[T, E]]  →  Result[list[T], E]
```

This matters because:

- **Fail-fast semantics**: Stop on the first `Nothing` or `Err`
- **All-or-nothing results**: Either all succeed or you get the first failure
- **Composable pipelines**: Work with collections of fallible operations

### The Problem: Nested Loops and Checks

```python
def fetch_all_users(ids: list[int]) -> list[User]:
    results = []
    for id in ids:
        user = fetch_user(id)  # Returns Option[User]
        if user.is_none():
            return []  # What if one fails?
        results.append(user.unwrap())
    return results

# Messy, error-prone, hard to read
```

### The Traverse Solution

```python
from fptk.adt.traverse import traverse_option

def fetch_all_users(ids: list[int]) -> Option[list[User]]:
    return traverse_option(ids, fetch_user)
    # Returns Some([users...]) if all succeed
    # Returns NOTHING if any fails
```

One line, clear semantics, composable with other Option operations.

## API

### Sequence Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `sequence_option(xs)` | `Iterable[Option[A]] -> Option[list[A]]` | Collect Some values |
| `sequence_result(xs)` | `Iterable[Result[A, E]] -> Result[list[A], E]` | Collect Ok values |

### Traverse Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `traverse_option(xs, f)` | `(Iterable[A], A -> Option[B]) -> Option[list[B]]` | Map and collect |
| `traverse_result(xs, f)` | `(Iterable[A], A -> Result[B, E]) -> Result[list[B], E]` | Map and collect |

### Async Variants

| Function | Signature | Description |
|----------|-----------|-------------|
| `traverse_option_async(xs, f)` | `async (Iterable[A], A -> Awaitable[Option[B]]) -> Option[list[B]]` | Async map and collect |
| `traverse_result_async(xs, f)` | `async (Iterable[A], A -> Awaitable[Result[B, E]]) -> Result[list[B], E]` | Async map and collect |

## How It Works

### Sequence

Sequence iterates through the collection, accumulating values. On the first failure, it short-circuits:

```python
def sequence_option(xs):
    out = []
    for x in xs:
        if isinstance(x, Some):
            out.append(x.value)
        else:
            return NOTHING  # Short-circuit
    return Some(out)
```

### Traverse

Traverse is sequence composed with map—apply the function, then sequence:

```python
def traverse_option(xs, f):
    out = []
    for x in xs:
        result = f(x)
        if isinstance(result, Some):
            out.append(result.value)
        else:
            return NOTHING  # Short-circuit
    return Some(out)
```

Conceptually: `traverse(xs, f) = sequence(map(f, xs))`, but implemented more efficiently.

### Fail-Fast Behavior

All operations are **fail-fast**: they stop processing as soon as they encounter a failure. This means:

- Efficient: No wasted computation after a failure
- First error only: You get the first `Err`, not all of them
- For accumulating all errors, use [`validate_all`](validate.md)

## Examples

### Parsing a List of Inputs

```python
from fptk.adt.traverse import traverse_option
from fptk.adt.option import Some, NOTHING

def parse_int(s: str) -> Option[int]:
    try:
        return Some(int(s))
    except ValueError:
        return NOTHING

# Parse all or none
inputs = ["1", "2", "3"]
result = traverse_option(inputs, parse_int)
# Some([1, 2, 3])

inputs = ["1", "oops", "3"]
result = traverse_option(inputs, parse_int)
# NOTHING (stops at "oops")
```

### Fetching Multiple Resources

```python
from fptk.adt.traverse import traverse_result
from fptk.adt.result import Ok, Err

def fetch_user(id: int) -> Result[User, str]:
    user = db.get(id)
    if user:
        return Ok(user)
    return Err(f"User {id} not found")

# Fetch all users
ids = [1, 2, 3]
result = traverse_result(ids, fetch_user)
# Ok([User(1), User(2), User(3)]) or Err("User X not found")
```

### Validating Configuration

```python
from fptk.adt.traverse import sequence_result

def validate_field(name: str, value: str) -> Result[str, str]:
    if not value:
        return Err(f"{name} is required")
    return Ok(value)

# Validate multiple fields
validations = [
    validate_field("name", config.get("name", "")),
    validate_field("email", config.get("email", "")),
    validate_field("password", config.get("password", "")),
]

result = sequence_result(validations)
# Ok(["Alice", "alice@example.com", "secret"]) or Err("email is required")
```

### Combining with Option Methods

```python
from fptk.adt.traverse import traverse_option
from fptk.adt.option import from_nullable

def get_user_names(data: list[dict]) -> Option[list[str]]:
    return traverse_option(
        data,
        lambda d: from_nullable(d.get("name"))
    )

users = [{"name": "Alice"}, {"name": "Bob"}]
get_user_names(users)  # Some(["Alice", "Bob"])

users = [{"name": "Alice"}, {"age": 30}]
get_user_names(users)  # NOTHING (second has no name)
```

### Async Traversal

```python
from fptk.adt.traverse import traverse_result_async

async def fetch_user_async(id: int) -> Result[User, str]:
    try:
        user = await db.async_get(id)
        return Ok(user) if user else Err(f"User {id} not found")
    except Exception as e:
        return Err(str(e))

async def fetch_all_users(ids: list[int]) -> Result[list[User], str]:
    return await traverse_result_async(ids, fetch_user_async)

# Fetches sequentially (not in parallel)
# For parallel, see gather_results in async_tools
```

### Chaining Traversals

```python
from fptk.adt.traverse import traverse_result
from fptk.core.func import pipe

def process_batch(ids: list[int]) -> Result[list[ProcessedItem], str]:
    return pipe(
        ids,
        lambda xs: traverse_result(xs, fetch_item),       # Fetch all
        lambda r: r.bind(lambda items:
            traverse_result(items, validate_item)          # Validate all
        ),
        lambda r: r.bind(lambda items:
            traverse_result(items, transform_item)         # Transform all
        ),
    )
```

### From Sequence to Traverse

```python
from fptk.adt.traverse import sequence_option, traverse_option

# These are equivalent:
# 1. Manual map + sequence
options = [parse_int(s) for s in strings]  # list[Option[int]]
result = sequence_option(options)           # Option[list[int]]

# 2. Traverse (more efficient, no intermediate list)
result = traverse_option(strings, parse_int)
```

## Traverse vs validate_all

| Operation | Behavior | Use When |
|-----------|----------|----------|
| `traverse_result` | Fail-fast, returns first error | You only need one error |
| `validate_all` | Accumulates all errors | You want to show all problems |

```python
# Fail-fast: stops at first error
traverse_result(["bad1", "bad2"], parse_positive)
# Err("'bad1' is not positive")

# Accumulate: collects all errors
validate_all([check_positive, check_even], -3)
# Err(NonEmptyList("not positive", "not even"))
```

## When to Use Traverse

**Use traverse when:**

- You have a collection of values to process uniformly
- Each processing step might fail
- You want all-or-nothing semantics
- You want the first error, not all errors

**Use validate_all when:**

- You want to collect all errors
- You're validating user input
- Showing all problems at once is better UX

**Use gather_results when:**

- You need parallel async execution
- Each task is independent

## See Also

- [`Option`](option.md) — The underlying optional type
- [`Result`](result.md) — The underlying result type
- [`validate_all`](validate.md) — For accumulating all errors
- [`gather_results`](async.md) — For parallel async operations
