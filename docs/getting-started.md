# Getting Started

This guide introduces the core ideas of functional programming through fptk. We'll focus on understanding *why* these patterns exist, not just how to use them.

## Installation

```bash
pip install fptk
```

## Thinking in Transformations

The biggest shift in functional programming is thinking about code as **data transformations** rather than **instructions to execute**.

Consider this imperative code:

```python
def process_order(order):
    validated = validate_order(order)
    if not validated:
        return None

    total = calculate_total(validated)
    tax = apply_tax(total)

    result = save_order(tax)
    if not result:
        return None

    send_confirmation(result)
    return result
```

This code tells the computer *what to do* step by step. It's full of intermediate variables, None checks, and implicit control flow.

Now think of it as a transformation pipeline:

```
order → validate → calculate_total → apply_tax → save → send_confirmation → result
```

Each step transforms data into a new form. This is what `pipe` expresses:

```python
from fptk.core.func import pipe

def process_order(order):
    return pipe(
        order,
        validate_order,
        calculate_total,
        apply_tax,
        save_order,
        send_confirmation
    )
```

The code now reads like the transformation it represents. Adding, removing, or reordering steps is trivial.

## Pure Functions: The Foundation

A **pure function** has two properties:

1. **Same input → same output**: `add(2, 3)` always returns `5`
2. **No side effects**: It doesn't modify anything outside itself

Why does this matter? Because pure functions are:

- **Testable**: No mocks needed, just assert `f(input) == expected_output`
- **Cacheable**: If `f(x)` always returns the same thing, you can cache it
- **Parallelizable**: No shared state means no race conditions
- **Composable**: You can combine them freely without surprises

Most bugs come from shared mutable state. Pure functions eliminate this entire category of bugs.

```python
# Impure: modifies external state
total = 0
def add_to_total(x):
    global total
    total += x  # Side effect!
    return total

# Pure: no side effects
def add(a, b):
    return a + b
```

fptk helps you write pure functions by providing tools to handle the things that usually require impurity: errors, missing values, state, and effects.

## Option: Making Absence Explicit

In most languages, any value can be `null` or `None`. This leads to defensive programming:

```python
if user is not None:
    if user.profile is not None:
        if user.profile.name is not None:
            print(user.profile.name)
```

The problem isn't None itself—it's that None is *implicit*. Any function might return None, and the type system doesn't warn you.

**Option** makes absence explicit. A value is either `Some(value)` or `Nothing`:

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Explicit: this might be absent
maybe_name: Option[str] = from_nullable(get_name())

# You must handle both cases
name = maybe_name.unwrap_or("Anonymous")
```

The power comes from **chaining**. Instead of nested None checks:

```python
# Without Option
if user and user.get("profile") and user.get("profile").get("email"):
    email = user["profile"]["email"].lower()
else:
    email = None
```

You compose transformations that automatically handle absence:

```python
# With Option
email = (
    from_nullable(user)
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("email")))
    .map(str.lower)
)
```

If any step returns `Nothing`, the rest of the chain is skipped. No None checks needed.

### Key Insight: map vs bind

- `map(f)` transforms the value inside: `Some(5).map(lambda x: x * 2)` → `Some(10)`
- `bind(f)` chains computations that might fail: when `f` itself returns an Option

```python
Some(5).map(lambda x: x * 2)           # Some(10) - f returns a value
Some(5).bind(lambda x: Some(x * 2))    # Some(10) - f returns an Option
Some(5).map(lambda x: Some(x * 2))     # Some(Some(10)) - wrong!
```

## Result: Errors as Values

Exceptions have a problem: they're invisible. Looking at a function signature, you can't tell if it might fail:

```python
def parse_config(path: str) -> dict:  # Might raise FileNotFoundError, JSONDecodeError, ...
    ...
```

You either wrap everything in try/except or discover errors at runtime.

**Result** makes errors explicit. A computation either succeeds with `Ok(value)` or fails with `Err(error)`:

```python
from fptk.adt.result import Ok, Err, Result

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' is not a valid integer")
```

The return type `Result[int, str]` tells you: this returns an int, but might fail with a string error.

Like Option, Result supports chaining:

```python
def process_input(raw: str) -> Result[int, str]:
    return (
        parse_int(raw)
        .map(lambda x: x * 2)
        .bind(validate_positive)
        .map(lambda x: x + 10)
    )
```

If any step fails, the error propagates automatically. No try/except nesting.

### Railway Oriented Programming

Think of Result as a railway with two tracks:

```
         ┌─ Ok ──→ map ──→ bind ──→ Ok result
Input ───┤
         └─ Err ─────────────────→ Err result
```

Once you're on the error track, you stay there. This is called "railway oriented programming" and it makes error handling composable.

## Validation: Accumulating Errors

Normal error handling is fail-fast: the first error stops everything.

```python
def validate(data):
    if not data.get("email"):
        return Err("Email required")  # Stops here
    if not data.get("name"):
        return Err("Name required")   # Never reached
    ...
```

For user-facing validation, you want to show *all* errors at once. `validate_all` accumulates them:

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err

result = validate_all([
    lambda d: Ok(d) if d.get("email") else Err("Email required"),
    lambda d: Ok(d) if d.get("name") else Err("Name required"),
    lambda d: Ok(d) if len(d.get("password", "")) >= 8 else Err("Password too short"),
], data)

# Err(NonEmptyList("Email required", "Name required", "Password too short"))
```

This is an example of **applicative** style, where independent computations can be combined. It's different from **monadic** style (`bind`), where each step depends on the previous.

## Composition: Building Complex from Simple

The goal of functional programming is to build complex behavior by composing simple pieces.

**compose** combines functions:

```python
from fptk.core.func import compose

# f(g(x))
inc_then_double = compose(lambda x: x * 2, lambda x: x + 1)
inc_then_double(5)  # 12
```

**curry** lets you partially apply functions:

```python
from fptk.core.func import curry

@curry
def send_email(to, subject, body):
    ...

# Create specialized functions
send_alert = send_email("alerts@company.com")("ALERT")
send_alert("Server is down!")
```

These tools let you build an application from small, reusable, testable pieces.

## When to Use fptk

**Good fit:**

- Data transformation pipelines
- Validation and parsing
- Error handling that needs to be explicit
- Code that needs to be highly testable
- Teams learning functional programming

**Start small:**

You don't need to rewrite your codebase. Start with:

1. Use `pipe` for one complex function
2. Use `Result` for one error-prone operation
3. Use `Option` for one nullable chain

Each pattern provides immediate value on its own.

## Next Steps

- [Core Concepts](guide/core-concepts.md) — Detailed guide to each pattern
- [Side Effects](guide/side-effects.md) — How to structure applications with pure cores
- [Migration Guide](guide/migration.md) — Step-by-step adoption from imperative code
- [Reference](reference/index.md) — Complete documentation with theory and examples
