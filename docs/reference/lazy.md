# Lazy Iterators

`fptk.iter.lazy` provides lazy iterator utilities for memory-efficient data processing.

## Concept: Lazy Evaluation

Lazy evaluation delays computation until the result is actually needed. With lazy iterators, you can build transformation pipelines that process data one element at a time, without loading entire collections into memory.

```python
# Eager: loads all 1M items, creates intermediate lists
doubled = [x * 2 for x in million_items]
filtered = [x for x in doubled if x > 100]
result = list(filtered)[:10]  # We only needed 10!

# Lazy: processes one at a time, stops after 10
from fptk.iter.lazy import map_iter, filter_iter
pipeline = filter_iter(
    lambda x: x > 100,
    map_iter(lambda x: x * 2, million_items)
)
result = list(islice(pipeline, 10))  # Only computes what's needed
```

This matters because:

- **Memory efficiency**: Process datasets larger than RAM
- **Early termination**: Stop processing when you have enough results
- **Composable pipelines**: Chain transformations without intermediate allocations

### The Problem: Eager Evaluation

```python
# Each step creates a full list in memory
users = load_all_users()              # 1M users in memory
active = [u for u in users if u.active]  # Another list
emails = [u.email for u in active]        # Another list
domains = [e.split("@")[1] for e in emails]  # Another list

# Memory usage: O(4N)
```

### The Lazy Solution

```python
from fptk.iter.lazy import map_iter, filter_iter

# Nothing loads yet—just builds a pipeline
pipeline = map_iter(
    lambda u: u.email.split("@")[1],
    filter_iter(lambda u: u.active, load_users_iterator())
)

# Only now do we consume, one item at a time
for domain in pipeline:
    print(domain)

# Memory usage: O(1) per item
```

## API

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `map_iter(f, xs)` | `(A -> B, Iterable[A]) -> Iterator[B]` | Lazy map |
| `filter_iter(pred, xs)` | `(A -> bool, Iterable[A]) -> Iterator[A]` | Lazy filter |
| `chunk(xs, n)` | `(Iterable[T], int) -> Iterator[tuple[T, ...]]` | Split into chunks |
| `group_by_key(xs, key)` | `(Iterable[T], T -> K) -> Iterator[tuple[K, list[T]]]` | Group consecutive items |

## How It Works

### `map_iter`

Lazily applies a function to each item:

```python
def map_iter(f, xs):
    for x in xs:
        yield f(x)
```

Uses a generator—no list is created. Values are computed one at a time when iterated.

### `filter_iter`

Lazily filters items by a predicate:

```python
def filter_iter(pred, xs):
    for x in xs:
        if pred(x):
            yield x
```

Only yields items that pass the predicate.

### `chunk`

Splits an iterable into fixed-size chunks:

```python
def chunk(xs, size):
    it = iter(xs)
    while True:
        buf = tuple(islice(it, size))
        if not buf:
            return
        yield buf
```

The last chunk may be smaller. Useful for batch processing.

### `group_by_key`

Groups consecutive items by a key function:

```python
def group_by_key(xs, key):
    for k, grp in groupby(xs, key=key):
        yield k, list(grp)
```

**Important**: Input must be pre-sorted by the key for correct results.

## Examples

### Basic Lazy Pipeline

```python
from fptk.iter.lazy import map_iter, filter_iter

# Build a lazy pipeline
numbers = range(1000000)  # Lazy range
doubled = map_iter(lambda x: x * 2, numbers)
big = filter_iter(lambda x: x > 100000, doubled)

# Nothing computed yet!

# Take only what we need
from itertools import islice
first_10 = list(islice(big, 10))
# Only computed ~50000 items to get 10 results
```

### Processing Large Files

```python
from fptk.iter.lazy import map_iter, filter_iter

def process_large_csv(path: str):
    with open(path) as f:
        # Skip header
        next(f)

        # Lazy pipeline
        lines = map_iter(str.strip, f)
        non_empty = filter_iter(bool, lines)
        rows = map_iter(lambda l: l.split(","), non_empty)
        valid = filter_iter(lambda r: len(r) == 3, rows)

        # Process one at a time
        for row in valid:
            yield process_row(row)
```

### Batch Database Inserts

```python
from fptk.iter.lazy import chunk

def batch_insert(records, batch_size=1000):
    """Insert records in batches to avoid memory issues."""
    for batch in chunk(records, batch_size):
        db.insert_many(batch)
        print(f"Inserted {len(batch)} records")
```

### Paginated API Calls

```python
from fptk.iter.lazy import chunk

def fetch_with_pagination(ids: list[int], page_size=100):
    """Fetch resources in pages."""
    for page in chunk(ids, page_size):
        response = api.fetch_batch(list(page))
        yield from response["items"]
```

### Grouping Log Entries

```python
from fptk.iter.lazy import group_by_key

def process_logs_by_hour(log_entries):
    """Process logs grouped by hour."""
    # Sort by timestamp first (required for group_by_key)
    sorted_logs = sorted(log_entries, key=lambda e: e.timestamp)

    for hour, entries in group_by_key(sorted_logs, lambda e: e.timestamp.hour):
        print(f"Hour {hour}: {len(entries)} entries")
        process_hour_batch(entries)
```

### Combining with Result

```python
from fptk.iter.lazy import map_iter, filter_iter
from fptk.adt.result import Ok, Err

def parse_line(line: str) -> Result[Record, str]:
    try:
        return Ok(Record.parse(line))
    except ValueError as e:
        return Err(str(e))

def process_file(path: str):
    with open(path) as f:
        # Parse each line
        results = map_iter(parse_line, f)

        # Filter to successful parses
        valid = filter_iter(lambda r: r.is_ok(), results)

        # Extract values
        records = map_iter(lambda r: r.unwrap(), valid)

        for record in records:
            process(record)
```

### Lazy ETL Pipeline

```python
from fptk.iter.lazy import map_iter, filter_iter, chunk

def etl_pipeline(source_path: str, dest_db):
    """Extract-Transform-Load with lazy processing."""

    # Extract: read file lazily
    with open(source_path) as f:
        raw_lines = map_iter(str.strip, f)

        # Transform: parse and validate
        parsed = map_iter(parse_json, raw_lines)
        valid = filter_iter(lambda r: r.is_ok(), parsed)
        records = map_iter(lambda r: r.unwrap(), valid)
        transformed = map_iter(transform_record, records)

        # Load: batch inserts
        for batch in chunk(transformed, 500):
            dest_db.insert_many(batch)
```

### Combining Multiple Iterators

```python
from fptk.iter.lazy import map_iter, filter_iter
from itertools import chain

# Combine multiple sources lazily
source1 = load_csv("file1.csv")
source2 = load_csv("file2.csv")
source3 = load_csv("file3.csv")

# chain is lazy too
all_records = chain(source1, source2, source3)

# Apply common processing
processed = map_iter(normalize, filter_iter(is_valid, all_records))
```

### Memory-Efficient Aggregation

```python
from fptk.iter.lazy import map_iter

def streaming_average(numbers):
    """Compute average without storing all numbers."""
    total = 0
    count = 0
    for n in numbers:
        total += n
        count += 1
    return total / count if count > 0 else 0

# Process billions of numbers with O(1) memory
avg = streaming_average(map_iter(float, huge_file))
```

## Lazy vs Eager

| Aspect | Lazy (Iterator) | Eager (List) |
|--------|-----------------|--------------|
| Memory | O(1) per item | O(n) all at once |
| Start time | Instant | Must process all first |
| Multiple passes | Must recreate | Can iterate again |
| Random access | No | Yes |
| Debugging | Harder (consumed) | Easier (can inspect) |

## When to Use Lazy Iterators

**Use lazy iterators when:**

- Processing large datasets that don't fit in memory
- You might not need all results (early termination)
- Building pipelines of transformations
- Reading from files or streams
- Memory efficiency is important

**Use eager lists when:**

- You need random access
- You need to iterate multiple times
- The dataset is small
- You need to know the length upfront
- Debugging is a priority

## Built-in Python Alternatives

fptk's lazy functions wrap Python builtins with explicit typing:

| fptk | Python builtin |
|------|---------------|
| `map_iter(f, xs)` | `map(f, xs)` |
| `filter_iter(p, xs)` | `filter(p, xs)` |
| `chunk(xs, n)` | `itertools.batched(xs, n)` (3.12+) |
| `group_by_key(xs, k)` | `itertools.groupby(xs, k)` |

fptk versions provide better type hints and consistent API style.

## See Also

- [Data Processing Example](../examples/data-processing.md) — Lazy processing in ETL pipelines
- [`traverse`](traverse.md) — For working with collections of Option/Result
- [`async_tools`](async.md) — For async batch processing
