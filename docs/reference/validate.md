# Validation

`fptk.validate` provides applicative validation—running multiple checks and accumulating all errors instead of failing fast.

## Concept: Applicative Validation

Standard monadic composition (using `bind`) is **fail-fast**: the first error stops the chain. But for validation, you often want to **accumulate all errors** to show the user everything that's wrong at once.

```
Monadic (fail-fast):     check1 → Err → stop
Applicative (accumulate): check1 → Err, check2 → Err, check3 → Ok → Err([e1, e2])
```

This matters because:

- **Better UX**: Show all validation errors at once, not one at a time
- **Complete feedback**: Users can fix everything in one pass
- **Separate concerns**: Validation logic stays independent and composable

### The Problem: Fail-Fast Validation

```python
def validate_user(data: dict) -> Result[User, str]:
    return (
        check_name(data)
        .bind(lambda _: check_email(data))
        .bind(lambda _: check_age(data))
        .map(lambda _: User(**data))
    )

# If name is invalid, we never see email/age errors
result = validate_user({"name": "", "email": "bad", "age": -5})
# Err("Name is required") — but email and age are also wrong!
```

### The Applicative Solution

```python
from fptk.validate import validate_all

def validate_user(data: dict) -> Result[User, NonEmptyList[str]]:
    return validate_all(
        [check_name, check_email, check_age],
        data
    ).map(lambda d: User(**d))

result = validate_user({"name": "", "email": "bad", "age": -5})
# Err(NonEmptyList("Name is required", "Invalid email", "Age must be positive"))
```

All checks run, all errors collected.

## API

### Function

```python
from fptk.validate import validate_all

def validate_all(
    checks: Iterable[Callable[[T], Result[T, E]]],
    value: T
) -> Result[T, NonEmptyList[E]]
```

**Parameters:**

- `checks`: Iterable of validation functions, each taking a value and returning `Result[T, E]`
- `value`: The value to validate

**Returns:**

- `Ok(value)` if all checks pass
- `Err(NonEmptyList[E])` containing all errors if any check fails

## How It Works

### Implementation

```python
def validate_all(checks, value):
    errors = None
    cur = value

    for check in checks:
        result = check(cur)
        if isinstance(result, Ok):
            cur = result.value  # Allow transformations
        elif isinstance(result, Err):
            err = result.error
            if errors is None:
                errors = NonEmptyList(err)
            else:
                errors = errors.append(err)

    return Ok(cur) if errors is None else Err(errors)
```

Key points:

1. **All checks run**: Unlike `bind`, we don't stop on first error
2. **Errors accumulate**: Collected into a `NonEmptyList`
3. **Value can transform**: If a check returns `Ok(transformed)`, subsequent checks use that
4. **NonEmptyList guarantee**: If we return `Err`, there's at least one error

### Validators as Functions

Each validator is a function `T -> Result[T, E]`:

```python
def required(field: str) -> Callable[[dict], Result[dict, str]]:
    def check(data: dict) -> Result[dict, str]:
        if data.get(field):
            return Ok(data)
        return Err(f"{field} is required")
    return check
```

## Examples

### Form Validation

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err

# Define validators
def required(field: str):
    def check(data: dict):
        if data.get(field):
            return Ok(data)
        return Err(f"{field} is required")
    return check

def email_format(field: str):
    def check(data: dict):
        email = data.get(field, "")
        if "@" in email and "." in email:
            return Ok(data)
        return Err(f"{field} must be a valid email")
    return check

def min_length(field: str, n: int):
    def check(data: dict):
        value = data.get(field, "")
        if len(value) >= n:
            return Ok(data)
        return Err(f"{field} must be at least {n} characters")
    return check

def age_range(min_age: int, max_age: int):
    def check(data: dict):
        age = data.get("age")
        if age is None:
            return Ok(data)  # Optional field
        if not isinstance(age, int):
            return Err("age must be a number")
        if min_age <= age <= max_age:
            return Ok(data)
        return Err(f"age must be between {min_age} and {max_age}")
    return check

# Use validators
def validate_signup(form: dict) -> Result[dict, NonEmptyList[str]]:
    return validate_all([
        required("username"),
        required("email"),
        required("password"),
        email_format("email"),
        min_length("username", 3),
        min_length("password", 8),
        age_range(13, 120),
    ], form)

# Test it
bad_form = {
    "username": "ab",
    "email": "not-an-email",
    "password": "123",
    "age": 10,
}

result = validate_signup(bad_form)
# Err(NonEmptyList(
#   "email must be a valid email",
#   "username must be at least 3 characters",
#   "password must be at least 8 characters",
#   "age must be between 13 and 120"
# ))
```

### API Request Validation

```python
from fptk.validate import validate_all
from fptk.core.func import pipe

def validate_request(request: dict) -> Result[dict, NonEmptyList[str]]:
    return validate_all([
        # Required fields
        required("method"),
        required("path"),

        # Method validation
        lambda r: (
            Ok(r) if r.get("method") in ["GET", "POST", "PUT", "DELETE"]
            else Err("Invalid HTTP method")
        ),

        # Path validation
        lambda r: (
            Ok(r) if r.get("path", "").startswith("/")
            else Err("Path must start with /")
        ),

        # Body validation for POST/PUT
        lambda r: (
            Ok(r) if r.get("method") not in ["POST", "PUT"] or r.get("body")
            else Err("Body required for POST/PUT")
        ),
    ], request)

# Handle the result
def process_request(request: dict):
    return validate_request(request).match(
        ok=lambda r: handle_valid_request(r),
        err=lambda errors: {
            "status": 400,
            "errors": list(errors)
        }
    )
```

### Reusable Validator Library

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err
import re

# Generic validators
def is_string(field: str):
    return lambda d: (
        Ok(d) if isinstance(d.get(field), str)
        else Err(f"{field} must be a string")
    )

def is_int(field: str):
    return lambda d: (
        Ok(d) if isinstance(d.get(field), int)
        else Err(f"{field} must be an integer")
    )

def matches(field: str, pattern: str, message: str):
    regex = re.compile(pattern)
    return lambda d: (
        Ok(d) if regex.match(d.get(field, ""))
        else Err(message)
    )

def one_of(field: str, options: list):
    return lambda d: (
        Ok(d) if d.get(field) in options
        else Err(f"{field} must be one of: {', '.join(map(str, options))}")
    )

def depends_on(field: str, condition_field: str, condition_value):
    """field is required when condition_field == condition_value"""
    return lambda d: (
        Ok(d) if d.get(condition_field) != condition_value or d.get(field)
        else Err(f"{field} is required when {condition_field} is {condition_value}")
    )

# Compose validators
user_validators = [
    required("name"),
    is_string("name"),
    min_length("name", 2),

    required("email"),
    matches("email", r"^[\w.-]+@[\w.-]+\.\w+$", "Invalid email format"),

    one_of("role", ["admin", "user", "guest"]),

    depends_on("department", "role", "admin"),
]
```

### Transforming During Validation

Validators can transform the data:

```python
def normalize_email(data: dict) -> Result[dict, str]:
    """Lowercase and strip the email."""
    if "email" in data:
        normalized = {**data, "email": data["email"].lower().strip()}
        return Ok(normalized)
    return Ok(data)

def trim_strings(data: dict) -> Result[dict, str]:
    """Strip whitespace from all string fields."""
    return Ok({
        k: v.strip() if isinstance(v, str) else v
        for k, v in data.items()
    })

result = validate_all([
    trim_strings,      # Transform first
    normalize_email,
    required("email"),
    email_format("email"),
], form)
# The validation runs on normalized data
```

### Nested Validation

```python
def validate_address(data: dict) -> Result[dict, NonEmptyList[str]]:
    return validate_all([
        required("street"),
        required("city"),
        required("country"),
        lambda d: (
            Ok(d) if len(d.get("postal_code", "")) >= 5
            else Err("Postal code must be at least 5 characters")
        ),
    ], data)

def validate_user_with_address(data: dict) -> Result[dict, NonEmptyList[str]]:
    # Validate user fields
    user_result = validate_all([
        required("name"),
        required("email"),
    ], data)

    # Validate nested address
    address_result = validate_address(data.get("address", {}))

    # Combine results
    match (user_result, address_result):
        case (Ok(_), Ok(_)):
            return Ok(data)
        case (Err(e1), Ok(_)):
            return Err(e1)
        case (Ok(_), Err(e2)):
            return Err(e2)
        case (Err(e1), Err(e2)):
            # Combine error lists
            combined = e1
            for e in e2:
                combined = combined.append(f"address.{e}")
            return Err(combined)
```

## When to Use validate_all

**Use validate_all when:**

- You want to show all validation errors at once
- Validating user input (forms, API requests)
- Each validation is independent
- Better UX is important

**Use bind chain when:**

- Validations depend on each other
- You only need the first error
- Short-circuit behavior is desired

## validate_all vs traverse_result

| Function | Error Behavior | Return Type |
|----------|---------------|-------------|
| `traverse_result` | Fail-fast (first error) | `Result[list[T], E]` |
| `validate_all` | Accumulate all errors | `Result[T, NonEmptyList[E]]` |

```python
# traverse_result: stop at first error
traverse_result(["bad1", "bad2"], parse)
# Err("bad1 is invalid")

# validate_all: collect all errors
validate_all([check1, check2, check3], value)
# Err(NonEmptyList("error1", "error2"))
```

## See Also

- [`Result`](result.md) — The underlying Result type
- [`NonEmptyList`](nelist.md) — The error collection type
- [`traverse_result`](traverse.md) — For fail-fast collection processing
- [API Development Recipe](../recipes/api-development.md) — Validation in web APIs
