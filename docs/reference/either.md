# Either

`fptk.adt.either` provides `Either[L, R]`, a symmetric sum type representing one of two possible values. Unlike `Result` which has success/error semantics, `Either` is neutral—both `Left` and `Right` are equally valid alternatives.

## Concept: Symmetric Alternatives

While `Result[T, E]` implies "success or failure," `Either[L, R]` simply means "one or the other." Use `Either` when both possibilities are valid outcomes, not errors.

```python
Either[L, R] = Left[L] | Right[R]
```

### When to Use Either vs Result

| Type | Use When |
|------|----------|
| `Result[T, E]` | One path is "success," the other is "failure" |
| `Either[L, R]` | Both paths are valid alternatives |

### Example: Parsing with Two Valid Outcomes

```python
from fptk.adt.either import Either, Left, Right

def parse_id(s: str) -> Either[int, str]:
    """Parse as integer ID, or keep as string name."""
    if s.isdigit():
        return Left(int(s))
    return Right(s)

# Both outcomes are valid
parse_id("123")   # Left(123) - numeric ID
parse_id("alice") # Right("alice") - string name
```

## API

### Types

| Type | Description |
|------|-------------|
| `Either[L, R]` | Sum type: either `Left[L]` or `Right[R]` |
| `Left[L, R]` | Left variant containing value of type `L` |
| `Right[L, R]` | Right variant containing value of type `R` |

### Constructors

```python
from fptk.adt.either import Left, Right

left_value = Left(42)        # Left[int, ???]
right_value = Right("hello") # Right[???, str]
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_left()` | `() -> bool` | True if Left |
| `is_right()` | `() -> bool` | True if Right |
| `map_left(f)` | `(L -> L2) -> Either[L2, R]` | Transform Left value |
| `map_right(f)` | `(R -> R2) -> Either[L, R2]` | Transform Right value |
| `bimap(f, g)` | `(L -> L2, R -> R2) -> Either[L2, R2]` | Transform both sides |
| `fold(on_left, on_right)` | `(L -> T, R -> T) -> T` | Pattern match to single value |
| `swap()` | `() -> Either[R, L]` | Flip Left ↔ Right |

## Examples

### Basic Usage

```python
from fptk.adt.either import Either, Left, Right

# Create values
left: Either[int, str] = Left(42)
right: Either[int, str] = Right("hello")

# Check variant
left.is_left()   # True
right.is_right() # True
```

### Transforming Values

```python
# map_left transforms Left, passes through Right
Left(5).map_left(lambda x: x * 2)     # Left(10)
Right("hi").map_left(lambda x: x * 2) # Right("hi")

# map_right transforms Right, passes through Left
Right("hi").map_right(str.upper)     # Right("HI")
Left(5).map_right(str.upper)         # Left(5)

# bimap transforms whichever side is present
Left(2).bimap(lambda x: x + 1, str.upper)   # Left(3)
Right("a").bimap(lambda x: x + 1, str.upper) # Right("A")
```

### Pattern Matching with fold

```python
def describe(e: Either[int, str]) -> str:
    return e.fold(
        on_left=lambda n: f"Got number: {n}",
        on_right=lambda s: f"Got string: {s}"
    )

describe(Left(42))      # "Got number: 42"
describe(Right("hello")) # "Got string: hello"
```

### Swapping Sides

```python
Left(1).swap()  # Right(1)
Right("a").swap() # Left("a")

# Double swap returns to original
e = Left(5)
e.swap().swap() == e  # True
```

### Chaining Transformations

```python
result = (
    Left(5)
    .map_left(lambda x: x * 2)   # Left(10)
    .map_left(lambda x: x + 1)   # Left(11)
    .map_right(str.upper)        # Still Left(11)
)

result2 = (
    Right("hello")
    .map_left(lambda x: x * 2)   # Still Right("hello")
    .map_right(str.upper)        # Right("HELLO")
    .map_right(lambda s: s + "!") # Right("HELLO!")
)
```

### Real-World Example: Configuration Sources

```python
from fptk.adt.either import Either, Left, Right

def get_config(key: str) -> Either[str, dict]:
    """Get config from env var (Left) or config file (Right)."""
    import os

    env_value = os.getenv(key)
    if env_value:
        return Left(env_value)

    # Fall back to config file
    return Right(load_config_file())

# Handle both sources uniformly
config = get_config("DATABASE_URL")
connection_string = config.fold(
    on_left=lambda env: env,  # Use env var directly
    on_right=lambda cfg: cfg.get("database", {}).get("url", "")
)
```

### Real-World Example: Parse or Keep Original

```python
from fptk.adt.either import Either, Left, Right
import json

def try_parse_json(s: str) -> Either[dict, str]:
    """Parse as JSON or keep as raw string."""
    try:
        return Left(json.loads(s))
    except json.JSONDecodeError:
        return Right(s)

# Process based on what we got
def handle_input(s: str) -> str:
    return try_parse_json(s).fold(
        on_left=lambda d: f"Got JSON with {len(d)} keys",
        on_right=lambda s: f"Got raw string: {s[:20]}..."
    )
```

## Either vs Result

```python
from fptk.adt.either import Left, Right
from fptk.adt.result import Ok, Err

# Result: success/failure semantics
def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("division by zero")  # This is an error
    return Ok(a / b)                     # This is success

# Either: two valid alternatives
def classify(n: int) -> Either[int, int]:
    if n % 2 == 0:
        return Left(n)   # Even numbers
    return Right(n)      # Odd numbers
    # Neither is "wrong"—they're just different categories
```

## See Also

- [`Result`](result.md) — Success/failure with typed errors
- [`Option`](option.md) — Optional values
