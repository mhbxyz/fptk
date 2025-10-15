# Getting Started with fptk

Welcome to fptk! This guide will get you up and running in 15 minutes. We'll start with a simple example and build from there.

## Installation

Install fptk using pip:

```bash
pip install fptk
```

For development:
```bash
pip install -e .[dev]
```

## Your First Pipeline

Let's start with a common problem: deeply nested function calls that are hard to read.

**Before (nested calls):**
```python
def process_request(request):
    return send_notification(
        format_message(
            validate_data(
                parse_json(request)
            )
        )
    )
```

**After (with fptk):**
```python
from fptk.core.func import pipe

def process_request(request):
    return pipe(
        request,
        parse_json,
        validate_data,
        format_message,
        send_notification
    )
```

The `pipe()` function threads your data through each function in order. It's more readable and easier to modify.

## Why Use fptk?

fptk helps you write:
- **More readable code**: Linear data flow instead of nested calls
- **Better error handling**: Explicit error types instead of exceptions everywhere
- **Testable code**: Pure functions that don't have side effects
- **Composable code**: Functions that easily work together

## Quick Examples

### Error Handling with Result

Instead of try/except everywhere:

```python
from fptk.adt.result import Ok, Err, Result

def divide(a: int, b: int) -> Result[int, str]:
    if b == 0:
        return Err("Cannot divide by zero")
    return Ok(a // b)

# Chain operations safely
result = pipe(
    divide(10, 2),
    lambda x: x.bind(lambda val: divide(val, 5)),
    lambda x: x.map(lambda val: f"Result: {val}")
)
# Result: Ok("Result: 1")
```

### Handling Missing Data with Option

No more None checks:

```python
from fptk.adt.option import Some, NOTHING, from_nullable

def get_user_name(user_data: dict) -> str:
    return (
        from_nullable(user_data.get('profile'))
        .bind(lambda profile: from_nullable(profile.get('name')))
        .unwrap_or('Anonymous')
    )

print(get_user_name({'profile': {'name': 'Alice'}}))  # Alice
print(get_user_name({}))  # Anonymous
```

### Working with Collections

Lazy processing of large datasets:

```python
from fptk.iter.lazy import map_iter, filter_iter

numbers = range(1000000)  # Large dataset

# Process lazily - no memory issues
even_squares = pipe(
    numbers,
    lambda xs: filter_iter(lambda x: x % 2 == 0, xs),
    lambda xs: map_iter(lambda x: x * x, xs),
    lambda xs: list(xs)  # Convert to list when needed
)
```

## When Should You Use fptk?

**Good fit:**
- Processing pipelines (data, requests, workflows)
- Error-prone operations (parsing, validation, I/O)
- Complex business logic
- Async operations with error handling

**Maybe not:**
- Simple scripts with few functions
- Performance-critical code (micro-optimizations)
- When your team prefers imperative style

## Next Steps

1. **Read the Core Concepts** to understand the main ideas
2. **Try the Recipes** for practical examples
3. **Check the Migration Guide** to adopt fptk gradually

Remember: you don't need to use everything at once. Start with `pipe()` and add features as you need them!