# Writer

`fptk.adt.writer` provides the `Writer` monad for computations that produce a value alongside an accumulated log. It separates the "what to compute" from the "what to record" concerns.

## Concept: The Writer Monad

The Writer monad represents computations that produce both a value and a log that accumulates across operations. The log can be any **monoid**—a type with an identity element and an associative combine operation.

Think of it as: **a computation that keeps a running log**.

```python
Writer[W, A]  ≈  (A, W)  # where W is a Monoid
```

A `Writer[list[str], int]` is a computation that produces an `int` while accumulating a list of log messages.

### The Problem: Logging Mixed with Logic

```python
def process(data, logger):
    logger.info("Starting processing")
    validated = validate(data)
    logger.debug(f"Validated: {validated}")
    transformed = transform(validated)
    logger.debug(f"Transformed: {transformed}")
    logger.info("Processing complete")
    return transformed

# Problems:
# - Logger pollutes function signatures
# - Side effects interleaved with pure logic
# - Hard to test without mocking logger
```

### The Writer Solution

```python
from fptk.adt.writer import Writer, tell, monoid_list

def process(data) -> Writer[list[str], Result]:
    return (
        Writer.unit(data, monoid_list)
        .bind(lambda d: tell(["Starting processing"]).map(lambda _: d))
        .bind(lambda d:
            tell([f"Validated: {validate(d)}"]).map(lambda _: validate(d))
        )
        .bind(lambda v:
            tell([f"Transformed: {transform(v)}"]).map(lambda _: transform(v))
        )
        .bind(lambda t:
            tell(["Processing complete"]).map(lambda _: t)
        )
    )

# Pure: no side effects until we extract
result, logs = process(data).run()
# Then write logs however we want
for log in logs:
    print(log)
```

The computation is pure. Logs are collected, not written. We can inspect, filter, or redirect them.

## Concept: Monoids

A **monoid** is a type with:

1. An **identity element** (empty value): `e`
2. An **associative combine operation**: `combine(a, combine(b, c)) == combine(combine(a, b), c)`

Common monoids:

| Type | Identity | Combine |
|------|----------|---------|
| `list` | `[]` | `+` (concatenation) |
| `str` | `""` | `+` (concatenation) |
| `int` (sum) | `0` | `+` (addition) |
| `int` (product) | `1` | `*` (multiplication) |

fptk provides:

```python
from fptk.adt.writer import monoid_list, monoid_str

monoid_list  # identity=[], combine=lambda a, b: a + b
monoid_str   # identity="", combine=lambda a, b: a + b
```

## API

### Types

| Type | Description |
|------|-------------|
| `Writer[W, A]` | Computation producing `A` with log `W` |
| `Monoid[W]` | Protocol with `identity` and `combine` |

### Constructor

```python
from fptk.adt.writer import Writer, monoid_list

# Create with empty log
w = Writer.unit(42, monoid_list)

# Create with value and initial log
w = Writer(42, ["started"], monoid_list)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `unit(value, monoid)` | `classmethod` | Create with empty log |
| `map(f)` | `(A -> B) -> Writer[W, B]` | Transform the value |
| `bind(f)` | `(A -> Writer[W, B]) -> Writer[W, B]` | Chain, combining logs |
| `run()` | `() -> (A, W)` | Extract value and log |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `tell(log, monoid)` | `(W, Monoid[W]) -> Writer[W, None]` | Add to the log |
| `listen(writer)` | `Writer[W, A] -> Writer[W, (A, W)]` | Get value and log as pair |
| `censor(f, writer)` | `(W -> W, Writer[W, A]) -> Writer[W, A]` | Modify the log |

### Monoid Requirements

Some functions require a monoid parameter, others don't:

| Function | Needs Monoid? | Why |
|----------|---------------|-----|
| `Writer(v, log, m)` | Yes | Creates new Writer |
| `Writer.unit(v, m)` | Yes | Creates new Writer |
| `tell(log, m)` | Yes | Creates new Writer |
| `listen(w)` | No | Uses existing Writer's monoid |
| `censor(f, w)` | No | Uses existing Writer's monoid |

Functions that **create** a Writer need the monoid to know how to combine logs later. Functions that **operate on** an existing Writer already have access to its monoid.

```python
from fptk.adt.writer import Writer, tell, listen, censor, monoid_list

# Creating Writers - need monoid
w1 = Writer.unit(5, monoid_list)
w2 = tell(["log entry"], monoid_list)

# Operating on existing Writers - monoid comes from the Writer
w3 = listen(w1)                          # Uses w1's monoid
w4 = censor(lambda logs: logs[-1:], w1)  # Uses w1's monoid
```

### Built-in Monoids

fptk provides predefined monoids for common use cases:

| Monoid | Type | Identity | Description |
|--------|------|----------|-------------|
| `monoid_list` | `list[object]` | `[]` | List concatenation |
| `monoid_str` | `str` | `""` | String concatenation |
| `monoid_sum` | `int \| float` | `0` | Numeric addition |
| `monoid_product` | `int \| float` | `1` | Numeric multiplication |
| `monoid_all` | `bool` | `True` | Logical AND (conjunction) |
| `monoid_any` | `bool` | `False` | Logical OR (disjunction) |
| `monoid_set` | `frozenset[object]` | `frozenset()` | Set union |
| `monoid_max` | `float` | `-inf` | Maximum value |
| `monoid_min` | `float` | `+inf` | Minimum value |

```python
from fptk.adt.writer import (
    monoid_list, monoid_str, monoid_sum, monoid_product,
    monoid_all, monoid_any, monoid_set, monoid_max, monoid_min,
)

# Accumulate counts
monoid_sum.combine(5, 3)  # 8

# Track boolean conditions
monoid_all.combine(True, False)  # False
monoid_any.combine(True, False)  # True

# Collect unique items
monoid_set.combine(frozenset({1, 2}), frozenset({2, 3}))  # frozenset({1, 2, 3})

# Track extremes
monoid_max.combine(5.0, 10.0)  # 10.0
monoid_min.combine(5.0, 10.0)  # 5.0
```

## How It Works

### Data Structure

Writer stores a value, a log, and the monoid for combining logs:

```python
@dataclass(frozen=True, slots=True)
class Monoid[W]:
    identity: W
    combine: Callable[[W, W], W]

@dataclass(frozen=True, slots=True)
class Writer[W, A]:
    value: A
    log: W
    monoid: Monoid[W]

    @classmethod
    def unit(cls, value, monoid):
        return cls(value, monoid.identity, monoid)

    def run(self):
        return (self.value, self.log)
```

### The Functor: `map`

`map` transforms the value, preserving the log:

```python
def map(self, f):
    return Writer(f(self.value), self.log, self.monoid)
```

### The Monad: `bind`

`bind` sequences computations and combines their logs:

```python
def bind(self, f):
    wb = f(self.value)
    return Writer(
        wb.value,
        self.monoid.combine(self.log, wb.log),  # Combine logs!
        self.monoid
    )
```

Key insight: logs from both computations are combined using the monoid's `combine` operation.

### Writer Operations

```python
def tell(log, monoid):
    """Add to log, return None as value."""
    return Writer(None, log, monoid)

def listen(writer):
    """Get value and log as a pair."""
    return Writer((writer.value, writer.log), writer.log, writer.monoid)

def censor(f, writer):
    """Apply f to modify the log."""
    return Writer(writer.value, f(writer.log), writer.monoid)
```

## Examples

### Simple Logging

```python
from fptk.adt.writer import Writer, tell, monoid_list

def double(x: int) -> Writer[list[str], int]:
    result = x * 2
    return tell([f"Doubled {x} to {result}"], monoid_list).map(lambda _: result)

def add_ten(x: int) -> Writer[list[str], int]:
    result = x + 10
    return tell([f"Added 10 to {x}, got {result}"], monoid_list).map(lambda _: result)

# Chain operations
result = (
    Writer.unit(5, monoid_list)
    .bind(double)
    .bind(add_ten)
)

value, logs = result.run()
# value = 20
# logs = ["Doubled 5 to 10", "Added 10 to 10, got 20"]
```

### Metrics Collection

```python
from dataclasses import dataclass

@dataclass
class Metrics:
    db_queries: int = 0
    cache_hits: int = 0
    api_calls: int = 0

    def __add__(self, other):
        return Metrics(
            self.db_queries + other.db_queries,
            self.cache_hits + other.cache_hits,
            self.api_calls + other.api_calls
        )

monoid_metrics = Monoid(
    identity=Metrics(),
    combine=lambda a, b: a + b
)

def record_db_query() -> Writer[Metrics, None]:
    return tell(Metrics(db_queries=1), monoid_metrics)

def record_cache_hit() -> Writer[Metrics, None]:
    return tell(Metrics(cache_hits=1), monoid_metrics)

def fetch_user(id: int) -> Writer[Metrics, User]:
    # Check cache first
    cached = cache.get(id)
    if cached:
        return record_cache_hit().map(lambda _: cached)

    # Query database
    user = db.query(id)
    return record_db_query().map(lambda _: user)

# Collect metrics across operations
result = (
    fetch_user(1)
    .bind(lambda u1: fetch_user(2).map(lambda u2: [u1, u2]))
    .bind(lambda users: fetch_user(3).map(lambda u3: users + [u3]))
)

users, metrics = result.run()
# metrics.db_queries = 2, metrics.cache_hits = 1, etc.
```

### Audit Trail

```python
from datetime import datetime

@dataclass
class AuditEntry:
    timestamp: datetime
    action: str
    user: str

def audit(action: str, user: str) -> Writer[list[AuditEntry], None]:
    entry = AuditEntry(datetime.now(), action, user)
    return tell([entry], monoid_list)

def transfer_funds(from_acc: str, to_acc: str, amount: float, user: str):
    return (
        audit(f"Started transfer of ${amount}", user)
        .bind(lambda _: debit(from_acc, amount))
        .bind(lambda _: audit(f"Debited {from_acc}", user))
        .bind(lambda _: credit(to_acc, amount))
        .bind(lambda _: audit(f"Credited {to_acc}", user))
        .bind(lambda _: audit("Transfer complete", user))
    )

_, audit_trail = transfer_funds("A", "B", 100, "alice").run()
# audit_trail contains all entries in order
```

### Using `censor` to Filter Logs

```python
def verbose_computation() -> Writer[list[str], int]:
    return (
        Writer.unit(0, monoid_list)
        .bind(lambda x: tell(["DEBUG: starting"], monoid_list).map(lambda _: x))
        .bind(lambda x: tell(["INFO: processing"], monoid_list).map(lambda _: x + 1))
        .bind(lambda x: tell(["DEBUG: intermediate"], monoid_list).map(lambda _: x))
        .bind(lambda x: tell(["INFO: done"], monoid_list).map(lambda _: x + 1))
    )

# Filter to only INFO level
def only_info(logs):
    return [l for l in logs if l.startswith("INFO")]

result = censor(only_info, verbose_computation())
value, logs = result.run()
# logs = ["INFO: processing", "INFO: done"]
```

### Using `listen` to Inspect Logs

```python
def computation_with_summary() -> Writer[list[str], str]:
    return (
        listen(verbose_computation())
        .map(lambda pair:
            f"Computed {pair[0]} with {len(pair[1])} log entries"
        )
    )

summary, logs = computation_with_summary().run()
# summary = "Computed 2 with 4 log entries"
# logs still contains all entries
```

### Using Built-in Monoids

fptk provides predefined monoids for common patterns. Here are examples using each:

#### Sum Monoid

Track cumulative values like costs, counts, or sizes:

```python
from fptk.adt.writer import Writer, tell, monoid_sum

def process_with_cost(data: list) -> Writer[int, list]:
    return tell(len(data), monoid_sum).map(lambda _: [x * 2 for x in data])

result = (
    Writer.unit([1, 2, 3], monoid_sum)
    .bind(process_with_cost)  # cost: 3
    .bind(process_with_cost)  # cost: 3
)

value, total_cost = result.run()
# value = [4, 8, 12], total_cost = 6
```

#### Max Monoid

Track peak values like maximum memory usage or highest latency:

```python
from fptk.adt.writer import Writer, tell, monoid_max

def track_max(value: float) -> Writer[float, float]:
    return tell(value, monoid_max).map(lambda _: value)

result = (
    track_max(5.0)
    .bind(lambda _: track_max(10.0))
    .bind(lambda _: track_max(3.0))
)

_, max_seen = result.run()
# max_seen = 10.0
```

#### Min Monoid

Track minimum values like lowest latency or smallest size:

```python
from fptk.adt.writer import Writer, tell, monoid_min

def track_min(value: float) -> Writer[float, float]:
    return tell(value, monoid_min).map(lambda _: value)

result = (
    track_min(5.0)
    .bind(lambda _: track_min(10.0))
    .bind(lambda _: track_min(3.0))
)

_, min_seen = result.run()
# min_seen = 3.0
```

#### Set Union Monoid

Collect unique items like tags, categories, or visited nodes:

```python
from fptk.adt.writer import Writer, tell, monoid_set

def tag(labels: set[str]) -> Writer[frozenset[str], None]:
    return tell(frozenset(labels), monoid_set)

result = (
    tag({"python", "fp"})
    .bind(lambda _: tag({"fp", "monad"}))
    .bind(lambda _: tag({"tutorial"}))
)

_, all_tags = result.run()
# all_tags = frozenset({"python", "fp", "monad", "tutorial"})
```

#### Product Monoid

Calculate combined probabilities or scaling factors:

```python
from fptk.adt.writer import Writer, tell, monoid_product

def scale(factor: float) -> Writer[float, float]:
    return tell(factor, monoid_product).map(lambda _: factor)

result = (
    scale(0.9)
    .bind(lambda _: scale(0.8))
    .bind(lambda _: scale(0.95))
)

_, combined_factor = result.run()
# combined_factor = 0.684 (0.9 * 0.8 * 0.95)
```

#### Boolean Monoids

Track conditions across computations:

```python
from fptk.adt.writer import Writer, tell, monoid_all, monoid_any

# monoid_all: All conditions must be True
def check_positive(x: int) -> Writer[bool, int]:
    return tell(x > 0, monoid_all).map(lambda _: x)

result = (
    check_positive(5)
    .bind(check_positive)
    .bind(lambda x: check_positive(x - 10))  # -5, fails
)

value, all_positive = result.run()
# all_positive = False (one check failed)

# monoid_any: At least one condition must be True
def check_even(x: int) -> Writer[bool, int]:
    return tell(x % 2 == 0, monoid_any).map(lambda _: x + 1)

result = (
    check_even(1)   # odd
    .bind(check_even)  # even!
    .bind(check_even)  # odd
)

value, any_even = result.run()
# any_even = True (one check passed)
```

### Custom Monoids

You can also create custom monoids for domain-specific types:

```python
from dataclasses import dataclass
from fptk.adt.writer import Monoid, Writer, tell

@dataclass
class Metrics:
    db_queries: int = 0
    cache_hits: int = 0

    def __add__(self, other):
        return Metrics(
            self.db_queries + other.db_queries,
            self.cache_hits + other.cache_hits
        )

monoid_metrics = Monoid(identity=Metrics(), combine=lambda a, b: a + b)

def record_db_query() -> Writer[Metrics, None]:
    return tell(Metrics(db_queries=1), monoid_metrics)
```

## When to Use Writer

**Use Writer when:**

- You want to accumulate logs/metrics alongside computations
- You need audit trails or tracing
- You want to separate logging concerns from business logic
- You need pure, testable logging

**Don't use Writer when:**

- Logs need to be written immediately (use effect systems)
- The log could grow unboundedly (memory issues)
- Simple cases where explicit logging is clearer

## Writer vs Other Patterns

| Pattern | When to Use |
|---------|-------------|
| Writer monad | Pure log accumulation, composable |
| Logger injection | When you need immediate I/O |
| Global logger | Simple applications (avoid for testability) |
| State monad | When you need to read/modify the log |

Writer is particularly useful for tracing, auditing, and collecting metrics in a pure, composable way.

## See Also

- [`Reader`](reader.md) — Read-only environment access
- [`State`](state.md) — Read and write state
- [Side Effects](../guide/side-effects.md) — Pure cores with effects at the edges
