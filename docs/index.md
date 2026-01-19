# fptk

Pragmatic functional programming for Python 3.12+.

## What is Functional Programming?

Functional programming is a way of writing code where you build programs by composing pure functions. Functions that always return the same output for the same input and don't modify anything outside themselves.

This sounds abstract, but it solves real problems:

- **Bugs from shared state**: When multiple parts of your code modify the same data, tracking down bugs becomes a nightmare. Pure functions don't modify anything, so this problem disappears.
- **Code that's hard to test**: Functions with side effects (database calls, API requests, file I/O) need complex mocks to test. Pure functions just need inputs and expected outputs.
- **Code that's hard to understand**: When a function can do anything—modify globals, call APIs, write files—you have to read the entire implementation to know what it does. Pure functions are predictable.

Functional programming isn't about using fancy abstractions. It's about writing code that's easier to reason about, test, and maintain.

## Why fptk?

Python is a great language, but it has some pain points that functional patterns solve elegantly:

### The `None` Problem

```python
user = get_user(id)
name = user.get("profile").get("name").upper()  # AttributeError
```

Python's `None` propagates silently until it explodes. You end up with defensive code everywhere:

```python
user = get_user(id)
if user and user.get("profile") and user.get("profile").get("name"):
    name = user["profile"]["name"].upper()
else:
    name = "Anonymous"
```

fptk's `Option` makes absence explicit and composable:

```python
name = (
    from_nullable(get_user(id))
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("name")))
    .map(str.upper)
    .unwrap_or("Anonymous")
)
```

### The Exception Problem

Exceptions are invisible in function signatures. You call `parse_json(data)` and have no idea it might raise `JSONDecodeError`, `UnicodeDecodeError`, or `MemoryError`. You either wrap everything in try/except or hope for the best.

fptk's `Result` makes errors part of the type:

```python
def parse_json(data: str) -> Result[dict, str]:
    ...

# The return type tells you: this can fail, handle it
```

### The Nested Calls Problem

Real code often looks like this:

```python
send_email(format_message(validate(parse(request))))
```

Reading order is inside-out. Adding a step means finding the right nesting level. fptk's `pipe` makes data flow linear:

```python
pipe(request, parse, validate, format_message, send_email)
```

## The Functional Mindset

Functional programming asks you to think differently:

| Imperative Thinking | Functional Thinking |
|---------------------|---------------------|
| "Do this, then do that" | "Transform this into that" |
| Modify variables in place | Create new values from old ones |
| Handle errors with try/catch | Make errors part of the return type |
| Check for None everywhere | Make absence explicit with Option |
| Functions can do anything | Functions only compute outputs from inputs |

This shift takes practice, but the payoff is code that's more predictable, testable, and composable.

## What fptk Provides

| Feature | What it solves |
|---------|----------------|
| `pipe`, `compose` | Nested function calls, hard-to-read data flow |
| `Option` | Null pointer errors, defensive None checks |
| `Result` | Invisible exceptions, unclear error handling |
| `validate_all` | Fail-fast validation, poor error messages |
| `Reader` | Dependency injection, config threading |
| `State` | Mutable state, hard-to-test stateful code |
| `Writer` | Logging mixed with logic, side effects |

## Installation

```bash
pip install fptk
```

## Next Steps

- [Getting Started](getting-started.md) — Understand the concepts and start using fptk
- **Guide**
    - [Core Concepts](guide/core-concepts.md) — Deep dive into each pattern
    - [Side Effects](guide/side-effects.md) — Structure code with pure cores
    - [Migration](guide/migration.md) — Gradually adopt functional patterns
- **Recipes**
    - [API Development](recipes/api-development.md) — Build robust web APIs
    - [Data Processing](recipes/data-processing.md) — ETL pipelines and transformations
- [API Reference](api.md) — Complete API documentation
