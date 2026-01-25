# Result

`fptk.adt.result` provides the `Result` type for handling operations that can succeed or fail. Instead of throwing exceptions, `Result` makes errors explicit and composable.

## Concept: The Either/Result Monad

In functional programming, `Result` (also called `Either` in Haskell) represents a computation that can succeed with a value or fail with an error. It has two cases:

- **Ok(value)**: The computation succeeded
- **Err(error)**: The computation failed

This matters because:

- **Explicit error handling**: The type signature tells you something can fail
- **Composable error paths**: Chain operations and handle all errors at the end
- **No hidden control flow**: No exceptions jumping through your call stack
- **Railway-oriented programming**: Success and error paths run in parallel tracks

### The Problem with Exceptions

```python
def process(data):
    parsed = json.loads(data)        # Might raise JSONDecodeError
    validated = validate(parsed)      # Might raise ValidationError
    result = transform(validated)     # Might raise TransformError
    return result

# Caller has no idea what might be thrown
try:
    result = process(data)
except json.JSONDecodeError as e:
    # Handle parse error
except ValidationError as e:
    # Handle validation error
except TransformError as e:
    # Handle transform error
```

### The Result Solution

```python
from fptk.adt.result import Ok, Err
from fptk.core.func import pipe

def process(data: str) -> Result[Output, str]:
    return pipe(
        data,
        parse_json,        # Returns Result[dict, str]
        lambda r: r.bind(validate),     # Result[Validated, str]
        lambda r: r.bind(transform),    # Result[Output, str]
    )

# Caller sees the Result type and handles it
result = process(data)
result.match(
    ok=lambda output: save(output),
    err=lambda error: log_error(error)
)
```

The error type is visible. Each step's error becomes part of the chain. One handling point at the end.

## API

### Types

| Type | Description |
|------|-------------|
| `Result[T, E]` | Base type: success `T` or error `E` |
| `Ok[T, E]` | Success variant containing value of type `T` |
| `Err[T, E]` | Failure variant containing error of type `E` |

### Constructors

```python
from fptk.adt.result import Ok, Err

success = Ok(42)
failure = Err("something went wrong")
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_ok()` | `() -> bool` | Returns `True` if `Ok` |
| `is_err()` | `() -> bool` | Returns `True` if `Err` |
| `map(f)` | `(T -> U) -> Result[U, E]` | Transform success value |
| `bind(f)` | `(T -> Result[U, E]) -> Result[U, E]` | Chain Result-returning functions |
| `and_then(f)` | `(T -> Result[U, E]) -> Result[U, E]` | Alias for `bind` (Rust naming) |
| `flatten()` | `Result[Result[T, E], E] -> Result[T, E]` | Unwrap nested Result |
| `zip(other)` | `(Result[U, E]) -> Result[tuple[T, U], E]` | Combine two Results into tuple |
| `zip_with(other, f)` | `(Result[U, E], (T, U) -> R) -> Result[R, E]` | Combine two Results with function |
| `map_err(f)` | `(E -> F) -> Result[T, F]` | Transform error value |
| `recover(f)` | `(E -> T) -> Result[T, E]` | Convert `Err` to `Ok` using function |
| `recover_with(f)` | `(E -> Result[T, E]) -> Result[T, E]` | Convert `Err` to another `Result` |
| `unwrap_or(default)` | `(U) -> T | U` | Get value or default |
| `unwrap_or_else(f)` | `(E -> U) -> T | U` | Get value or compute from error |
| `match(ok, err)` | `(T -> U, E -> U) -> U` | Pattern match both cases |
| `unwrap()` | `() -> T` | Get value or raise ValueError |
| `expect(msg)` | `(str) -> T` | Get value or raise with message |

### Async Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map_async(f)` | `async (T -> U) -> Result[U, E]` | Async transform success |
| `bind_async(f)` | `async (T -> Result[U, E]) -> Result[U, E]` | Async chain |

## How It Works

### Data Structure

`Result` is implemented as a sealed type with two variants:

```python
class Result[T, E]:
    """Base class - not instantiated directly."""
    pass

@dataclass(frozen=True, slots=True)
class Ok[T, E](Result[T, E]):
    value: T

@dataclass(frozen=True, slots=True)
class Err[T, E](Result[T, E]):
    error: E
```

### The Functor: `map`

`map` transforms the success value, leaving errors unchanged:

```python
def map(self, f):
    if isinstance(self, Ok):
        return Ok(f(self.value))
    return self  # Err passes through
```

### The Monad: `bind`

`bind` chains operations that return `Result`:

```python
def bind(self, f):
    if isinstance(self, Ok):
        return f(self.value)  # f returns Result[U, E]
    return self  # Err passes through
```

### The Bifunctor: `map_err`

Unlike `Option`, `Result` can transform its error too:

```python
def map_err(self, f):
    if isinstance(self, Err):
        return Err(f(self.error))
    return self  # Ok passes through
```

### Railway-Oriented Programming

Think of `Result` as a railway track with two rails:

```
     Ok path  ─────┬─────┬─────┬─────> Success
                   │     │     │
     Err path ─────┴─────┴─────┴─────> Failure
               parse  validate transform
```

Each function either continues on the Ok track or switches to the Err track. Once on the Err track, you stay there (errors propagate automatically).

## Examples

### Wrapping Exceptions

```python
from fptk.core.func import try_catch
from fptk.adt.result import Ok, Err

# Automatic wrapping
safe_parse = try_catch(json.loads)
safe_parse('{"a": 1}')  # Ok({"a": 1})
safe_parse('invalid')    # Err(JSONDecodeError(...))

# Manual wrapping
def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' is not a valid integer")
```

### Chaining Operations

```python
def validate_age(data: dict) -> Result[dict, str]:
    age = data.get("age")
    if age is None:
        return Err("age is required")
    if not isinstance(age, int):
        return Err("age must be an integer")
    if age < 0 or age > 150:
        return Err("age must be between 0 and 150")
    return Ok(data)

def validate_email(data: dict) -> Result[dict, str]:
    email = data.get("email")
    if not email or "@" not in email:
        return Err("valid email is required")
    return Ok(data)

def process_user(raw: str) -> Result[User, str]:
    return (
        try_catch(json.loads)(raw)
        .map_err(lambda e: f"Invalid JSON: {e}")
        .bind(validate_age)
        .bind(validate_email)
        .map(lambda d: User(**d))
    )
```

### Error Transformation

```python
# Convert detailed errors to user-friendly messages
def user_friendly_error(e: Exception) -> str:
    if isinstance(e, json.JSONDecodeError):
        return "The data format is invalid"
    if isinstance(e, ValidationError):
        return f"Please check your input: {e.field}"
    return "An unexpected error occurred"

result = (
    process_data(raw)
    .map_err(user_friendly_error)
)
```

### Pattern Matching

```python
def respond(result: Result[User, str]) -> Response:
    return result.match(
        ok=lambda user: Response(200, {"user": user.to_dict()}),
        err=lambda error: Response(400, {"error": error})
    )
```

### Fallback Values

```python
# Simple default
value = parse_int(input).unwrap_or(0)

# Computed default (only runs on error)
value = parse_int(input).unwrap_or_else(
    lambda err: log_and_return_default(err)
)
```

### Recovering from Errors

Use `recover` to convert an `Err` to `Ok` with a fallback value:

```python
from fptk.adt.result import Ok, Err

# Provide a default value on error
Err("not found").recover(lambda e: "default")  # Ok("default")
Ok(5).recover(lambda e: 0)  # Ok(5) - unchanged

# Practical example: config with fallback
def get_config(key: str) -> Result[str, str]:
    return read_config_file(key).recover(lambda e: default_config[key])
```

Use `recover_with` for conditional recovery where some errors can be handled:

```python
from fptk.adt.result import Ok, Err

def fetch_with_retry(url: str) -> Result[Response, str]:
    return fetch(url).recover_with(lambda e:
        fetch(url) if e == "timeout" else Err(e)  # Retry only timeouts
    )

# Chain multiple recovery strategies
result = (
    fetch_from_primary()
    .recover_with(lambda e: fetch_from_secondary())  # Try backup
    .recover(lambda e: cached_response)              # Last resort: cache
)
```

### Combining with Option

```python
from fptk.adt.option import from_nullable

def get_user_email(user_id: int) -> Result[str, str]:
    return (
        from_nullable(db.get(user_id))
        .to_result(f"User {user_id} not found")
        .bind(lambda user:
            from_nullable(user.get("email"))
            .to_result("User has no email")
        )
    )
```

### Flattening Nested Results

Use `flatten` when you have a `Result[Result[T, E], E]` and want `Result[T, E]`:

```python
from fptk.adt.result import Ok, Err

# Direct usage
Ok(Ok(42)).flatten()       # Ok(42)
Ok(Err("inner")).flatten() # Err("inner")
Err("outer").flatten()     # Err("outer")

# Common scenario: map with a function that returns Result
def fetch_user(id: int) -> Result[User, str]: ...
def fetch_permissions(user: User) -> Result[Permissions, str]: ...

# Without flatten: Result[Result[Permissions, str], str]
nested = fetch_user(1).map(fetch_permissions)

# With flatten: Result[Permissions, str]
permissions = fetch_user(1).map(fetch_permissions).flatten()

# Note: this is equivalent to using bind directly
permissions = fetch_user(1).bind(fetch_permissions)
```

## When to Use Result

**Use Result when:**

- An operation can fail and you want to handle the error
- You want typed errors instead of string exceptions
- You're building a pipeline where errors should propagate
- You want to force callers to acknowledge potential failures

**Don't use Result when:**

- Failure is truly exceptional (programming bugs, out of memory)
- You're in a hot loop and performance matters
- The error doesn't carry useful information → consider `Option`

## Comparison with Option

| Aspect | Option | Result |
|--------|--------|--------|
| Cases | `Some(T)`, `Nothing` | `Ok(T)`, `Err(E)` |
| Absence info | No | Yes (error type) |
| Use case | Value might not exist | Operation might fail |
| Convert to | `.to_result(err)` | N/A |

## See Also

- [`Option`](option.md) — When absence doesn't need error information
- [`try_catch`](core.md#try_catch) — Convert exceptions to Result
- [`validate_all`](validate.md) — Accumulate multiple errors
- [`traverse_result`](traverse.md) — Collect multiple Results into one
