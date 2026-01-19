# NonEmptyList

`fptk.adt.nelist` provides `NonEmptyList`, a list that is guaranteed to have at least one element by construction.

## Concept: Non-Empty Collections

Many operations on lists fail or produce meaningless results when the list is empty:

```python
max([])    # ValueError: max() arg is an empty sequence
min([])    # ValueError
head = xs[0]  # IndexError if empty
sum(xs) / len(xs)  # ZeroDivisionError if empty
```

A `NonEmptyList` makes non-emptiness a type-level guarantee. If you have a `NonEmptyList`, you know it has at least one element—no runtime checks needed.

### The Problem: Empty List Checks

```python
def average(xs: list[float]) -> float:
    if not xs:
        raise ValueError("Cannot compute average of empty list")
    return sum(xs) / len(xs)

def first(xs: list[T]) -> T:
    if not xs:
        raise ValueError("List is empty")
    return xs[0]

# Every function needs to validate, every caller needs to handle
```

### The NonEmptyList Solution

```python
from fptk.adt.nelist import NonEmptyList

def average(xs: NonEmptyList[float]) -> float:
    # No check needed—xs is guaranteed non-empty
    return sum(xs) / len(list(xs))

def first(xs: NonEmptyList[T]) -> T:
    return xs.head  # Always safe

# Construct safely
result = NonEmptyList.from_iter(data)  # Option[NonEmptyList]
if result:
    avg = average(result)
else:
    # Handle empty case once, at the boundary
```

## API

### Types

| Type | Description |
|------|-------------|
| `NonEmptyList[E]` | List with at least one element |

### Constructor

```python
from fptk.adt.nelist import NonEmptyList

# Direct construction (always non-empty)
nel = NonEmptyList(1)                    # [1]
nel = NonEmptyList(1, (2, 3, 4))         # [1, 2, 3, 4]

# From iterable (might be empty)
result = NonEmptyList.from_iter([1, 2])  # NonEmptyList or None
result = NonEmptyList.from_iter([])      # None
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `head` | `E` | First element (guaranteed to exist) |
| `tail` | `tuple[E, ...]` | Remaining elements (may be empty) |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `append(e)` | `(E) -> NonEmptyList[E]` | Add element at end |
| `to_list()` | `() -> list[E]` | Convert to regular list |
| `from_iter(it)` | `staticmethod (Iterable[E]) -> NonEmptyList[E] | None` | Create from iterable |
| `__iter__()` | `() -> Iterator[E]` | Iterate all elements |

## How It Works

### Data Structure

NonEmptyList stores a required `head` and optional `tail`:

```python
@dataclass(frozen=True, slots=True)
class NonEmptyList[E]:
    head: E                      # First element (required)
    tail: tuple[E, ...] = ()     # Remaining elements (tuple for immutability)
```

The `head` field is required, guaranteeing at least one element. The `tail` is a tuple (immutable) that may be empty.

### Safe Construction

```python
@staticmethod
def from_iter(it: Iterable[E]) -> NonEmptyList[E] | None:
    iterator = iter(it)
    try:
        h = next(iterator)
    except StopIteration:
        return None  # Empty iterable
    return NonEmptyList(h, tuple(iterator))
```

`from_iter` returns `None` for empty iterables—the only way to get a `NonEmptyList` is with at least one element.

### Iteration

```python
def __iter__(self):
    yield self.head
    yield from self.tail
```

Iterates in order: head first, then tail elements.

### Append

```python
def append(self, e: E) -> NonEmptyList[E]:
    return NonEmptyList(self.head, self.tail + (e,))
```

Returns a new `NonEmptyList` with the element added at the end (immutable).

## Examples

### Safe Head Access

```python
from fptk.adt.nelist import NonEmptyList

# Regular list: might fail
def unsafe_head(xs: list[int]) -> int:
    return xs[0]  # IndexError if empty!

# NonEmptyList: always safe
def safe_head(xs: NonEmptyList[int]) -> int:
    return xs.head  # Guaranteed to exist

# Construct at boundaries
data = get_data()  # list[int]
nel = NonEmptyList.from_iter(data)
if nel:
    print(safe_head(nel))
else:
    print("No data available")
```

### Computing Statistics

```python
from fptk.adt.nelist import NonEmptyList

def stats(xs: NonEmptyList[float]) -> dict:
    """Compute statistics. No empty-list checks needed."""
    values = list(xs)
    return {
        "count": len(values),
        "sum": sum(values),
        "mean": sum(values) / len(values),
        "min": min(values),  # Safe
        "max": max(values),  # Safe
        "first": xs.head,    # Safe
    }

# Safe construction
data = NonEmptyList.from_iter(measurements)
if data:
    result = stats(data)
```

### Building Results

```python
from fptk.adt.nelist import NonEmptyList

def collect_errors(validations: list[Result]) -> NonEmptyList[str] | None:
    """Collect error messages, if any."""
    errors = [r.error for r in validations if r.is_err()]
    return NonEmptyList.from_iter(errors)

# Later
errors = collect_errors(results)
if errors:
    # We know there's at least one error
    print(f"First error: {errors.head}")
    print(f"Total errors: {len(list(errors))}")
```

### With Validation

```python
from fptk.validate import validate_all
from fptk.adt.nelist import NonEmptyList

# validate_all returns Result[T, NonEmptyList[E]]
# If validation fails, you're guaranteed at least one error

result = validate_all([check1, check2, check3], data)
result.match(
    ok=lambda d: process(d),
    err=lambda errors: print(f"Validation failed: {errors.head}")
    # errors is NonEmptyList[str], so .head is safe
)
```

### Chaining Operations

```python
from fptk.adt.nelist import NonEmptyList

# Build up a list
nel = NonEmptyList(1)
nel = nel.append(2).append(3).append(4)

print(nel.head)       # 1
print(nel.tail)       # (2, 3, 4)
print(list(nel))      # [1, 2, 3, 4]
```

### Converting Collections

```python
from fptk.adt.nelist import NonEmptyList

# From various iterables
from_list = NonEmptyList.from_iter([1, 2, 3])
from_set = NonEmptyList.from_iter({1, 2, 3})
from_gen = NonEmptyList.from_iter(x for x in range(5))

# To list
nel = NonEmptyList(1, (2, 3))
regular_list = nel.to_list()  # [1, 2, 3]
```

## When to Use NonEmptyList

**Use NonEmptyList when:**

- Your domain requires at least one element
- You want to eliminate empty-list checks in downstream code
- You're accumulating errors (validation)
- Computing aggregates that require non-empty input (mean, max, etc.)

**Don't use NonEmptyList when:**

- Empty collections are valid in your domain
- You need frequent random access (use list)
- You need efficient append (tuple concatenation is O(n))

## NonEmptyList vs Option[list]

| Type | Meaning |
|------|---------|
| `list[T]` | Zero or more elements |
| `Option[list[T]]` | Maybe a list (but list could still be empty!) |
| `NonEmptyList[T]` | One or more elements (guaranteed) |
| `Option[NonEmptyList[T]]` | Maybe a non-empty list |

`NonEmptyList` is the right choice when you need to guarantee non-emptiness at the type level.

## See Also

- [`validate_all`](validate.md) — Uses NonEmptyList for error accumulation
- [`Option`](option.md) — For values that might be absent
- [`Result`](result.md) — For computations that might fail
