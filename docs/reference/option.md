# Option

`fptk.adt.option` provides the `Option` type for handling values that might be absent. Instead of using `None` and checking for it everywhere, `Option` makes absence explicit and composable.

## Concept: The Maybe/Option Monad

In functional programming, `Option` (also called `Maybe` in Haskell) represents a value that might not exist. It has two cases:

- **Some(value)**: The value is present
- **Nothing**: The value is absent

This matters because:

- **No null pointer exceptions**: You can't accidentally call methods on `None`
- **Explicit absence**: The type signature tells you a value might be missing
- **Composable transformations**: Chain operations that gracefully handle missing values

### The Problem with `None`

```python
user = get_user(id)
name = user.get("profile").get("name").upper()  # AttributeError if any is None!

# Defensive coding everywhere
if user and user.get("profile") and user.get("profile").get("name"):
    name = user["profile"]["name"].upper()
else:
    name = "Anonymous"
```

### The Option Solution

```python
from fptk.adt.option import from_nullable, Some, NOTHING

name = (
    from_nullable(get_user(id))
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("name")))
    .map(str.upper)
    .unwrap_or("Anonymous")
)
```

Each `.bind()` short-circuits to `NOTHING` if the previous step was absent. No exceptions, no nested conditionals.

## API

### Types

| Type | Description |
|------|-------------|
| `Option[T]` | Base type representing an optional value |
| `Some[T]` | Variant containing a present value |
| `Nothing` | Variant representing absence (singleton class) |
| `NOTHING` | The singleton instance of `Nothing` |

### Constructors

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Directly construct
present = Some(42)
absent = NOTHING

# From nullable value
from_nullable(some_value)  # Some(x) if x is not None, else NOTHING
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_some()` | `() -> bool` | Returns `True` if `Some` |
| `is_none()` | `() -> bool` | Returns `True` if `Nothing` |
| `map(f)` | `(T -> U) -> Option[U]` | Transform the value if present |
| `bind(f)` | `(T -> Option[U]) -> Option[U]` | Chain Option-returning functions |
| `zip(other)` | `(Option[U]) -> Option[tuple[T, U]]` | Combine two Options into tuple |
| `zip_with(other, f)` | `(Option[U], (T, U) -> R) -> Option[R]` | Combine two Options with function |
| `unwrap_or(default)` | `(U) -> T | U` | Get value or default |
| `or_else(alt)` | `(Option[T] | () -> Option[T]) -> Option[T]` | Alternative if absent |
| `to_result(err)` | `(E) -> Result[T, E]` | Convert to Result |
| `match(some, none)` | `(T -> U, () -> U) -> U` | Pattern match |
| `unwrap()` | `() -> T` | Get value or raise ValueError |
| `expect(msg)` | `(str) -> T` | Get value or raise with message |

### Async Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map_async(f)` | `async (T -> U) -> Option[U]` | Async transform |
| `bind_async(f)` | `async (T -> Option[U]) -> Option[U]` | Async chain |

## How It Works

### Data Structure

`Option` is implemented as a sealed type with two variants:

```python
class Option[T]:
    """Base class - not instantiated directly."""
    pass

@dataclass(frozen=True, slots=True)
class Some[T](Option[T]):
    value: T

@dataclass(frozen=True, slots=True)
class Nothing(Option[None]):
    pass

NOTHING = Nothing()  # Singleton
```

The `@dataclass(frozen=True, slots=True)` makes instances immutable and memory-efficient.

### The Functor: `map`

`map` applies a function to the value inside `Some`, or does nothing for `Nothing`:

```python
def map(self, f):
    if isinstance(self, Some):
        return Some(f(self.value))
    return NOTHING
```

This is the **Functor** operation: lifting a function `A -> B` to work on `Option[A] -> Option[B]`.

### The Monad: `bind`

`bind` (also called `flatMap` or `>>=`) chains operations that themselves return `Option`:

```python
def bind(self, f):
    if isinstance(self, Some):
        return f(self.value)  # f returns Option[U]
    return NOTHING
```

This is the **Monad** operation. It prevents nested `Option[Option[T]]` by "flattening" the result.

### Why `bind` vs `map`?

- Use `map` when your function returns a plain value: `lambda x: x + 1`
- Use `bind` when your function returns an `Option`: `lambda x: from_nullable(lookup(x))`

```python
# map: str -> str (plain value)
Some("hello").map(str.upper)  # Some("HELLO")

# bind: str -> Option[int] (returns Option)
Some("42").bind(lambda s: from_nullable(safe_parse(s)))  # Some(42) or NOTHING
```

## Examples

### Safe Dictionary Access

```python
from fptk.adt.option import from_nullable

config = {"database": {"host": "localhost", "port": 5432}}

# Chain lookups safely
port = (
    from_nullable(config.get("database"))
    .bind(lambda db: from_nullable(db.get("port")))
    .map(str)
    .unwrap_or("5432")
)
```

### Parsing User Input

```python
def parse_int(s: str) -> Option[int]:
    try:
        return Some(int(s))
    except ValueError:
        return NOTHING

def parse_positive(s: str) -> Option[int]:
    return parse_int(s).bind(
        lambda n: Some(n) if n > 0 else NOTHING
    )

parse_positive("42")   # Some(42)
parse_positive("-1")   # NOTHING
parse_positive("abc")  # NOTHING
```

### First-Available Value

```python
from fptk.adt.option import from_nullable, NOTHING

def get_config_value(key: str) -> Option[str]:
    """Try environment, then file, then default."""
    return (
        from_nullable(os.getenv(key))
        .or_else(lambda: from_nullable(config_file.get(key)))
        .or_else(lambda: from_nullable(defaults.get(key)))
    )
```

### Pattern Matching

```python
def describe(opt: Option[int]) -> str:
    return opt.match(
        some=lambda n: f"Got number: {n}",
        none=lambda: "No value"
    )

describe(Some(42))  # "Got number: 42"
describe(NOTHING)   # "No value"
```

### Converting to Result

```python
from fptk.adt.option import from_nullable

def find_user(id: int) -> Option[User]:
    return from_nullable(db.get(id))

# Convert to Result for error handling
result = find_user(42).to_result(f"User {id} not found")
# Ok(user) or Err("User 42 not found")
```

### Iteration

```python
from fptk.adt.option import Some, NOTHING

# Option implements __iter__ for zero-or-one elements
for value in Some(42):
    print(value)  # Prints 42

for value in NOTHING:
    print(value)  # Never executes
```

## When to Use Option

**Use Option when:**

- A value might legitimately be absent (not an error condition)
- You want to chain transformations that might fail
- You're parsing or looking up values that might not exist
- You want to avoid `None` checks scattered through your code

**Don't use Option when:**

- Absence represents an error that should be reported → use `Result`
- You need to know why a value is missing → use `Result` with error info
- Performance is critical in tight loops → Option has some overhead

## See Also

- [`Result`](result.md) — When absence is an error with information
- [`from_nullable`](#constructors) — Bridge from Python's `None` to `Option`
- [`traverse_option`](traverse.md) — Collect multiple Options into one
