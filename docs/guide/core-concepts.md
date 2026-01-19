# Core Concepts

This guide explains the main ideas behind fptk without getting too theoretical. We'll focus on practical usage with real examples.

## Functions as Building Blocks

fptk treats functions as reusable building blocks that you can combine in different ways.

### pipe(): Linear Data Flow

`pipe()` threads data through functions in sequence:

```python
from fptk.core.func import pipe

def process_user_data(raw_data):
    return pipe(
        raw_data,
        parse_json,      # Step 1: parse
        validate_user,   # Step 2: validate
        save_to_db,      # Step 3: save
        send_welcome     # Step 4: notify
    )
```

**Benefits:**

- Easy to read (top to bottom)
- Easy to add/remove steps
- Easy to test individual steps

### compose(): Function Building

`compose()` combines functions into new functions:

```python
from fptk.core.func import compose

# Create a new function from existing ones
process_and_save = compose(save_to_db, validate_user, parse_json)

# Use it
result = process_and_save(raw_data)
```

Note: `compose` applies functions right-to-left: `compose(f, g)(x)` = `f(g(x))`.

### curry(): Flexible Function Calls

`curry()` lets you call functions partially:

```python
from fptk.core.func import curry

def send_email(to, subject, body):
    # Send email logic
    pass

# Create specialized functions
send_support_email = curry(send_email)("support@company.com")
notify_user = send_support_email("Welcome!")

# Use them
notify_user("Welcome to our platform!")
```

## Handling Missing Data with Option

Python's `None` is error-prone. fptk's `Option` makes absence explicit.

### Basic Option Usage

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Convert potentially None values
name = from_nullable(user.get('name'))  # Some("Alice") or NOTHING

# Handle absence safely
display_name = name.map(lambda n: n.upper()).unwrap_or("Anonymous")
```

### Chaining Optional Operations

```python
def get_full_name(user):
    return (
        from_nullable(user.get('first_name'))
        .zip(from_nullable(user.get('last_name')))
        .map(lambda names: f"{names[0]} {names[1]}")
        .or_else(lambda: from_nullable(user.get('display_name')))
        .unwrap_or('Anonymous')
    )

get_full_name({'first_name': 'John', 'last_name': 'Doe'})  # "John Doe"
get_full_name({'display_name': 'Johnny'})                   # "Johnny"
get_full_name({})                                           # "Anonymous"
```

**Key Operations:**

| Method | Description |
|--------|-------------|
| `map(f)` | Transform the value if present |
| `bind(f)` | Chain operations that return Option |
| `or_else(f)` | Provide fallback Option |
| `unwrap_or(default)` | Get value or default |

## Error Handling with Result

Exceptions are great for unexpected errors, but for expected failures (validation, parsing, etc.), `Result` is clearer.

### Basic Result Usage

```python
from fptk.adt.result import Ok, Err, Result

def divide(a: int, b: int) -> Result[int, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a // b)

result = divide(10, 2)  # Ok(5)
error = divide(10, 0)   # Err("Division by zero")
```

### Chaining Results

```python
def process_payment(amount, card_number):
    return (
        validate_amount(amount)
        .bind(lambda amt: validate_card(card_number))
        .bind(lambda card: charge_card(amount, card))
    )

# Either Ok(success_data) or Err(error_message)
result = process_payment(100, "4111111111111111")
```

**Key Operations:**

| Method | Description |
|--------|-------------|
| `map(f)` | Transform success value |
| `bind(f)` | Chain operations returning Result |
| `map_err(f)` | Transform error |
| `unwrap_or(default)` | Get value or default |

## Working with Collections

fptk provides lazy utilities for processing collections efficiently.

### Lazy Processing

```python
from fptk.core.func import pipe
from fptk.iter.lazy import map_iter, filter_iter

# Process large datasets without loading everything
def process_logs(logs):
    return pipe(
        logs,
        lambda ls: filter_iter(lambda log: log['level'] == 'ERROR', ls),
        lambda ls: map_iter(lambda log: log['message'], ls),
        list
    )
```

### Grouping and Chunking

```python
from fptk.iter.lazy import group_by_key, chunk

# Group data by category (input must be sorted by key)
grouped = dict(group_by_key(users, lambda u: u['department']))

# Process in batches
for user_batch in chunk(users, 10):
    process_batch(user_batch)
```

## Async Operations

Handle concurrent operations with proper error handling.

### Gathering Results

```python
from fptk.async_tools import gather_results

async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    # Returns Ok([user_data]) or Err(first_error)
    return await gather_results(tasks)
```

### Async Pipelines

```python
from fptk.core.func import async_pipe

async def process_request(request):
    return await async_pipe(
        request,
        parse_async,
        validate_async,
        save_async,
        notify_async
    )
```

## Validation

Accumulate multiple validation errors instead of failing fast.

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user(user):
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email required"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Invalid email"),
        lambda u: Ok(u) if len(u.get('password', '')) >= 8 else Err("Password too short")
    ], user)

validate_user({'email': 'invalid', 'password': 'short'})
# Err(NonEmptyList("Invalid email", "Password too short"))
```

## Putting It All Together

Here's a complete example combining multiple concepts:

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def process_registration(data):
    return pipe(
        data,
        validate_registration,
        lambda valid: valid.bind(save_user),
        lambda saved: saved.bind(send_welcome_email),
        lambda result: result.map(lambda user: {
            'user_id': user['id'],
            'message': 'Registration successful'
        })
    )

def validate_registration(data):
    return validate_all([
        lambda d: Ok(d) if d.get('email') else Err("Email required"),
        lambda d: Ok(d) if d.get('password') else Err("Password required"),
    ], data)

# Usage
result = process_registration({
    'email': 'user@example.com',
    'password': 'secure123'
})
# Ok({'user_id': 123, 'message': 'Registration successful'})
```

This example shows how fptk concepts work together to create robust, readable code.
