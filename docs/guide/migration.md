# Migration Guide

This guide shows how to gradually adopt fptk patterns in your existing Python code. Each level builds on the previous one, so you can start small and add features as needed.

## Level 1: Function Composition

**Start here** — Replace nested function calls with `pipe()`.

### Before: Nested Calls

```python
def process_data(data):
    result = parse_json(data)
    if result:
        validated = validate_data(result)
        if validated:
            saved = save_to_db(validated)
            if saved:
                return format_response(saved)
    return None
```

### After: Linear Pipeline

```python
from fptk.core.func import pipe

def process_data(data):
    return pipe(
        data,
        parse_json,
        validate_data,
        save_to_db,
        format_response
    )
```

**Benefits:**

- ✅ Easier to read (top to bottom)
- ✅ Easier to add/remove steps
- ✅ Easier to test individual functions

## Level 2: Error Handling with Result

**Add proper error handling** — Replace exceptions and None checks with `Result`.

### Before: Exception Handling

```python
def create_user(email, password):
    try:
        if not validate_email(email):
            raise ValueError("Invalid email")
        hashed = hash_password(password)
        user_id = save_to_db(email, hashed)
        send_welcome_email(user_id)
        return user_id
    except Exception as e:
        log_error(e)
        return None
```

### After: Result-Based Flow

```python
from fptk.adt.result import Ok, Err
from fptk.core.func import pipe, try_catch

def create_user(email, password):
    return (
        validate_email_result(email)
        .bind(lambda _: hash_password_safe(password))
        .bind(lambda hashed: save_to_db_safe(email, hashed))
        .bind(send_welcome_email_safe)
    )

def validate_email_result(email):
    return Ok(email) if "@" in email else Err("Invalid email")

def hash_password_safe(password):
    return try_catch(lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()))()

def save_to_db_safe(email, hashed):
    return try_catch(lambda: db.save(email, hashed))()
```

**Benefits:**

- ✅ Explicit error types
- ✅ Composable error handling
- ✅ No exception bubbling

## Level 3: Optional Values with Option

**Handle missing data safely** — Replace None checks with `Option`.

### Before: None Checks Everywhere

```python
def get_display_name(user):
    if user.get('profile'):
        profile = user['profile']
        if profile.get('first_name') and profile.get('last_name'):
            return f"{profile['first_name']} {profile['last_name']}"
        elif profile.get('display_name'):
            return profile['display_name']
    return user.get('username', 'Anonymous')
```

### After: Option Chaining

```python
from fptk.adt.option import from_nullable

def get_display_name(user):
    return (
        from_nullable(user.get('profile'))
        .bind(lambda profile:
            from_nullable(profile.get('first_name'))
            .zip(from_nullable(profile.get('last_name')))
            .map(lambda names: f"{names[0]} {names[1]}")
            .or_else(lambda: from_nullable(profile.get('display_name')))
        )
        .or_else(lambda: from_nullable(user.get('username')))
        .unwrap_or('Anonymous')
    )
```

**Benefits:**

- ✅ No None-related bugs
- ✅ Explicit absence handling
- ✅ Composable operations

## Level 4: Validation Accumulation

**Collect all errors at once** — Replace fail-fast validation with error accumulation.

### Before: Fail-Fast Validation

```python
def validate_user(user):
    if not user.get('email'):
        return False, "Email required"
    if '@' not in user['email']:
        return False, "Invalid email"
    if len(user.get('password', '')) < 8:
        return False, "Password too short"
    return True, None
```

### After: Accumulate Errors

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user(user):
    return validate_all([
        lambda u: Ok(u) if u.get('email') else Err("Email required"),
        lambda u: Ok(u) if '@' in u.get('email', '') else Err("Invalid email"),
        lambda u: Ok(u) if len(u.get('password', '')) >= 8 else Err("Password too short"),
    ], user)
```

**Benefits:**

- ✅ All errors shown at once
- ✅ Better user experience
- ✅ Consistent validation API

## Level 5: Lazy Collections

**Process large datasets efficiently** — Replace lists with lazy iterators.

### Before: Loading Everything in Memory

```python
def process_logs(logs):
    errors = []
    for log in logs:
        if log['level'] == 'ERROR':
            parsed = parse_log_line(log['message'])
            if parsed:
                errors.append(parsed)
    return errors
```

### After: Lazy Processing

```python
from fptk.iter.lazy import map_iter, filter_iter

def process_logs(logs):
    return list(
        map_iter(parse_log_line,
            filter_iter(lambda log: log['level'] == 'ERROR', logs)
        )
    )
```

**Benefits:**

- ✅ Memory efficient for large datasets
- ✅ Composable processing steps
- ✅ Only processes what you need

## Level 6: Async Operations

**Handle concurrency safely** — Use `gather_results` for async operations.

### Before: Manual Async Coordination

```python
async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    data = []
    for result in results:
        if isinstance(result, Exception):
            log_error(result)
        else:
            data.append(result)
    return data
```

### After: Result-Based Concurrency

```python
from fptk.async_tools import gather_results

async def fetch_user_data(user_ids):
    tasks = [fetch_user_api(uid) for uid in user_ids]
    return await gather_results(tasks)
```

**Benefits:**

- ✅ Structured error handling
- ✅ Clean async code
- ✅ Consistent error types

## Common Migration Patterns

### Converting Exception-Based Code

```python
# Before
def risky_operation(x):
    if x < 0:
        raise ValueError("Negative value")
    return x * 2

# After
def risky_operation(x):
    return Ok(x * 2) if x >= 0 else Err("Negative value")
```

### Converting None-Returning Functions

```python
# Before
def find_user(user_id):
    return users_db.get(user_id)

# After
from fptk.adt.option import from_nullable

def find_user(user_id):
    return from_nullable(users_db.get(user_id))
```

### Converting Validation Functions

```python
# Before
def is_valid_email(email):
    return '@' in email

# After
def validate_email(email):
    return Ok(email) if '@' in email else Err("Invalid email")
```

## Migration Strategy

1. **Start Small**: Begin with `pipe()` in one function
2. **Add Error Handling**: Gradually convert exception-based functions to `Result`
3. **Handle Optionals**: Replace None checks with `Option`
4. **Build Up**: Add validation, async, and advanced patterns as needed

**Remember:**

- You don't need to convert everything at once
- Each level makes your code better
- Partial adoption is valuable
- Start with pain points in your codebase
