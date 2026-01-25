# Core Functions

`fptk.core.func` provides function combinators—small utilities that help you compose, transform, and control functions. These are the building blocks for functional programming in Python.

## Concept: Function Combinators

In functional programming, functions are values. Just like you can pass integers to functions and return them, you can pass functions to other functions and return new functions. **Function combinators** are higher-order functions that combine or transform functions.

This matters because:

- **Composition over inheritance**: Build complex behavior by combining simple functions
- **Point-free style**: Express transformations without naming intermediate values
- **Reusability**: Small functions compose into many different pipelines

## `pipe`

Thread a value through a sequence of functions, left-to-right.

```python
from fptk.core.func import pipe

def pipe(x, *funcs):
    """Thread a value through unary functions."""
```

### Why `pipe`?

Nested function calls read inside-out:

```python
# Hard to read: execution order is h(g(f(x)))
result = format_output(validate(parse_input(raw_data)))
```

`pipe` makes data flow linear and readable:

```python
# Clear: parse → validate → format
result = pipe(raw_data, parse_input, validate, format_output)
```

### How It Works

```python
def pipe(x, *funcs):
    for f in funcs:
        x = f(x)
    return x
```

Each function receives the output of the previous one. The implementation is a simple fold over the function list.

### Examples

```python
from fptk.core.func import pipe

# Basic transformation chain
result = pipe(
    "  hello world  ",
    str.strip,
    str.upper,
    lambda s: s.replace(" ", "_")
)
# result = "HELLO_WORLD"

# With Option for safe chaining
from fptk.adt.option import from_nullable

name = pipe(
    user_dict,
    lambda d: from_nullable(d.get("profile")),
    lambda opt: opt.bind(lambda p: from_nullable(p.get("name"))),
    lambda opt: opt.map(str.upper),
    lambda opt: opt.unwrap_or("Anonymous")
)
```

---

## `compose`

Combine two functions into one: `(f ∘ g)(x) = f(g(x))`.

```python
from fptk.core.func import compose

def compose(f, g):
    """Compose two unary functions: f(g(x))."""
```

### Why `compose`?

`compose` builds reusable function pipelines. Unlike `pipe` which applies to a value immediately, `compose` creates a new function you can use later.

```python
# Create a reusable transformation
normalize = compose(str.upper, str.strip)

# Apply it anywhere
normalize("  hello  ")  # "HELLO"
normalize("  world  ")  # "WORLD"
```

### How It Works

```python
def compose(f, g):
    def h(x):
        return f(g(x))
    return h
```

Mathematical function composition: apply `g` first, then `f`. This is the opposite order of `pipe`.

### Examples

```python
from fptk.core.func import compose

# Build transformation pipelines
strip_and_lower = compose(str.lower, str.strip)
strip_and_lower("  HELLO  ")  # "hello"

# Compose multiple functions (nested)
process = compose(
    lambda s: s.replace(" ", "_"),
    compose(str.upper, str.strip)
)
process("  hello world  ")  # "HELLO_WORLD"

# Use with higher-order functions
users = [" Alice ", " Bob "]
list(map(strip_and_lower, users))  # ["alice", "bob"]
```

---

## `curry`

Transform a function of N arguments into N nested functions of 1 argument.

```python
from fptk.core.func import curry

def curry(fn):
    """Curry a function of N positional args."""
```

### Why `curry`?

Currying enables **partial application**—supplying some arguments now and the rest later.

```python
# Without currying: need lambda
list(map(lambda x: add(1, x), [1, 2, 3]))

# With currying: cleaner
add = curry(lambda a, b: a + b)
list(map(add(1), [1, 2, 3]))  # [2, 3, 4]
```

### How It Works

```python
def curry(fn):
    def curried(*args, **kwargs):
        needed = fn.__code__.co_argcount
        if len(args) + len(kwargs) >= needed:
            return fn(*args, **kwargs)
        return lambda *a, **k: curried(*(args + a), **{**kwargs, **k})
    return curried
```

The curried function checks if enough arguments have been provided. If yes, call the original function. If no, return a new function that waits for more arguments.

### Examples

```python
from fptk.core.func import curry

# Basic currying
add = curry(lambda a, b: a + b)
add_one = add(1)
add_one(5)  # 6

# Three-argument function
format_name = curry(lambda first, middle, last: f"{first} {middle} {last}")
format_smith = format_name("John")("Q")
format_smith("Smith")  # "John Q Smith"

# Use with map/filter
multiply = curry(lambda a, b: a * b)
list(map(multiply(2), [1, 2, 3]))  # [2, 4, 6]
```

---

## `flip`

Swap the first two arguments of a binary function.

```python
from fptk.core.func import flip

def flip(fn):
    """Flip the first two arguments."""
```

### Why `flip`?

Sometimes a function has its arguments in the wrong order for your use case:

```python
# pow(base, exp) - but we want to map over bases with fixed exponent
list(map(lambda x: pow(x, 2), [1, 2, 3]))

# With flip
square = flip(pow)(2)  # flip makes it pow(exp, base)
list(map(square, [1, 2, 3]))  # [1, 4, 9]
```

### How It Works

```python
def flip(fn):
    def flipped(b, a):
        return fn(a, b)
    return flipped
```

Simply reverses the first two arguments.

### Examples

```python
from fptk.core.func import flip

# Flip division
div = lambda a, b: a / b
div(10, 2)  # 5.0

half_of = flip(div)(2)  # flipped: (2, x) -> x / 2
half_of(10)  # 5.0

# Flip string methods
append_to = flip(lambda s, suffix: s + suffix)
add_exclaim = append_to("!")
add_exclaim("hello")  # "hello!"
```

---

## `tap`

Run a side effect on a value and return the original value unchanged.

```python
from fptk.core.func import tap

def tap(f):
    """Run side effect, return input."""
```

### Why `tap`?

Debugging pipelines is tricky—you want to inspect values without changing them:

```python
result = pipe(
    data,
    parse,
    tap(print),  # See parsed data
    validate,
    tap(lambda x: logger.debug(f"Validated: {x}")),
    transform
)
```

### How It Works

```python
def tap(f):
    def inner(x):
        f(x)
        return x
    return inner
```

Call `f` for its side effect, ignore its return value, return the original input.

### Examples

```python
from fptk.core.func import tap, pipe

# Debug a pipeline
result = pipe(
    [1, 2, 3],
    lambda xs: [x * 2 for x in xs],
    tap(lambda xs: print(f"After doubling: {xs}")),
    sum
)
# Prints: After doubling: [2, 4, 6]
# result = 12

# Log without breaking flow
def log(msg):
    def logger(x):
        print(f"{msg}: {x}")
    return tap(logger)

pipe("hello", str.upper, log("uppercased"), str.title)
# Prints: uppercased: HELLO
# Returns: "Hello"
```

---

## `thunk`

Create a lazy, memoized computation. The function runs once, on first call.

```python
from fptk.core.func import thunk

def thunk(f):
    """Memoized nullary function (lazy value)."""
```

### Why `thunk`?

Delay expensive computations until needed, and cache the result:

```python
expensive_config = thunk(lambda: load_config_from_disk())

# Config isn't loaded yet...

result = expensive_config()  # Loads now
result2 = expensive_config()  # Returns cached value
```

### How It Works

```python
def thunk(f):
    evaluated = False
    value = None

    def wrapper():
        nonlocal evaluated, value
        if not evaluated:
            value = f()
            evaluated = True
        return value

    return wrapper
```

Classic memoization pattern: track if computed, store result, return cached value on subsequent calls.

### Examples

```python
from fptk.core.func import thunk

# Lazy configuration
config = thunk(lambda: {
    "db_url": os.getenv("DATABASE_URL"),
    "api_key": os.getenv("API_KEY")
})

# Expensive computation
fib_100 = thunk(lambda: compute_fibonacci(100))
# Not computed until first call
print(fib_100())  # Computes
print(fib_100())  # Returns cached
```

---

## `identity`

Return the input unchanged.

```python
from fptk.core.func import identity

def identity(x):
    """Return x unchanged."""
```

### Why `identity`?

Useful as a default function or placeholder in higher-order contexts:

```python
# Default transformation
transform = get_transform() or identity

# In Option.match
value = some_option.match(
    some=identity,  # Just return the value
    none=lambda: "default"
)
```

### How It Works

```python
def identity(x):
    return x
```

The simplest possible function.

---

## `const`

Create a function that ignores its arguments and always returns a fixed value.

```python
from fptk.core.func import const

def const(x):
    """Return a function that always returns x."""
```

### Why `const`?

Useful when an API expects a function but you want a fixed value:

```python
# Always return 0 for missing keys
default_factory = const(0)

# In Result.unwrap_or_else
result.unwrap_or_else(const("default"))
```

### How It Works

```python
def const(x):
    def inner(*_, **__):
        return x
    return inner
```

Captures `x` in a closure, ignores all arguments.

### Examples

```python
from fptk.core.func import const

always_zero = const(0)
always_zero(1, 2, 3)  # 0
always_zero("anything")  # 0

# Use in callbacks
list(map(const(1), [1, 2, 3]))  # [1, 1, 1]
```

---

## `once`

Wrap a function so it runs at most once. Subsequent calls return the first result.

```python
from fptk.core.func import once

def once(fn):
    """Run at most once, memoize first result."""
```

### Why `once`?

Ensure initialization code runs exactly once:

```python
init_database = once(lambda: create_db_connection())

# First call: connects
init_database()

# Subsequent calls: returns same connection
init_database()
```

### How It Works

```python
def once(fn):
    called = False
    result = None

    def wrapper(*args, **kwargs):
        nonlocal called, result
        if not called:
            result = fn(*args, **kwargs)
            called = True
        return result

    return wrapper
```

Like `thunk`, but accepts arguments (which are ignored after first call).

---

## `try_catch`

Convert exception-throwing functions to `Result`-returning functions.

```python
from fptk.core.func import try_catch

def try_catch(fn):
    """Wrap fn to return Ok/Err instead of raising."""
```

### Why `try_catch`?

Bridge between exception-based code and `Result`-based pipelines:

```python
# Standard library raises on invalid JSON
import json
json.loads("invalid")  # JSONDecodeError!

# Wrap to get Result
safe_parse = try_catch(json.loads)
safe_parse("invalid")  # Err(JSONDecodeError(...))
safe_parse('{"a": 1}')  # Ok({"a": 1})
```

### How It Works

```python
def try_catch(fn):
    def wrapper(*args, **kwargs):
        try:
            return Ok(fn(*args, **kwargs))
        except Exception as e:
            return Err(e)
    return wrapper
```

Catches `Exception` (not `BaseException`, to avoid catching `KeyboardInterrupt`/`SystemExit`).

### Examples

```python
from fptk.core.func import try_catch, pipe
from fptk.adt.result import Ok, Err

# Safe integer parsing
safe_int = try_catch(int)
safe_int("42")  # Ok(42)
safe_int("abc")  # Err(ValueError(...))

# In a pipeline
def process_input(raw: str):
    return pipe(
        raw,
        try_catch(json.loads),
        lambda r: r.map(extract_data),
        lambda r: r.bind(validate),
    )
```

---

## `async_pipe`

Async version of `pipe` that handles both sync and async functions.

```python
from fptk.core.func import async_pipe

async def async_pipe(x, *funcs):
    """Thread value through possibly-async functions."""
```

### How It Works

```python
async def async_pipe(x, *funcs):
    for f in funcs:
        x = f(x)
        if inspect.isawaitable(x):
            x = await x
    return x
```

Checks if each result is awaitable and awaits it if so. This allows mixing sync and async functions in the same pipeline.

### Examples

```python
from fptk.core.func import async_pipe

async def fetch_user(id):
    return await db.get_user(id)

def format_name(user):
    return user["name"].upper()

async def send_notification(name):
    await notifications.send(f"Hello, {name}")

# Mix sync and async
await async_pipe(
    user_id,
    fetch_user,      # async
    format_name,     # sync
    send_notification # async
)
```

---

## `foldl`

Left fold: reduce a collection from the left with an accumulator.

```python
from fptk.core.func import foldl

def foldl(f, init, xs):
    """Left fold: f(f(f(init, x1), x2), x3)"""
```

### Why `foldl`?

`foldl` is the fundamental operation for reducing collections. Many common operations (sum, product, max, min) are folds:

```python
# Sum is a fold
foldl(lambda acc, x: acc + x, 0, [1, 2, 3])  # 6

# Product is a fold
foldl(lambda acc, x: acc * x, 1, [1, 2, 3])  # 6
```

### How It Works

```python
def foldl(f, init, xs):
    acc = init
    for x in xs:
        acc = f(acc, x)
    return acc
```

Left fold processes elements left-to-right: `f(f(f(init, x1), x2), x3)`.

### Examples

```python
from fptk.core.func import foldl

# Sum
foldl(lambda acc, x: acc + x, 0, [1, 2, 3])  # 6

# Subtraction (left-associative): ((10-1)-2)-3 = 4
foldl(lambda acc, x: acc - x, 10, [1, 2, 3])  # 4

# Build string left-to-right
foldl(lambda acc, x: f"{acc}-{x}", "start", ["a", "b", "c"])
# "start-a-b-c"

# Flatten nested lists
foldl(lambda acc, x: acc + x, [], [[1, 2], [3], [4, 5]])
# [1, 2, 3, 4, 5]
```

---

## `foldr`

Right fold: reduce a collection from the right with an accumulator.

```python
from fptk.core.func import foldr

def foldr(f, init, xs):
    """Right fold: f(x1, f(x2, f(x3, init)))"""
```

### Why `foldr`?

Some operations are naturally right-associative. `foldr` preserves this structure:

```python
# Build a linked list (right-to-left)
foldr(lambda x, acc: (x, acc), None, [1, 2, 3])
# (1, (2, (3, None)))
```

### How It Works

```python
def foldr(f, init, xs):
    items = list(xs)
    acc = init
    for x in reversed(items):
        acc = f(x, acc)
    return acc
```

Right fold processes elements right-to-left: `f(x1, f(x2, f(x3, init)))`. Note that the accumulator is the second argument to `f`.

### Examples

```python
from fptk.core.func import foldr

# Build string right-to-left
foldr(lambda x, acc: f"{x}-{acc}", "end", ["a", "b", "c"])
# "a-b-c-end"

# Subtraction with right fold
# f(1, f(2, f(3, 10))) where f = lambda x, acc: acc - x
# = f(1, f(2, 7)) = f(1, 5) = 4
foldr(lambda x, acc: acc - x, 10, [1, 2, 3])  # 4

# Build nested structure
foldr(lambda x, acc: {"value": x, "next": acc}, None, [1, 2, 3])
# {"value": 1, "next": {"value": 2, "next": {"value": 3, "next": None}}}
```

---

## `reduce`

Reduce without initial value, returning `Option`.

```python
from fptk.core.func import reduce

def reduce(f, xs):
    """Reduce without init, returns Option."""
```

### Why `reduce`?

Sometimes the initial value should come from the collection itself. Python's built-in `functools.reduce` raises on empty collections. fptk's `reduce` returns `Option` for safety:

```python
from fptk.core.func import reduce

reduce(max, [1, 5, 3])  # Some(5)
reduce(max, [])          # NOTHING (no exception!)
```

### How It Works

```python
def reduce(f, xs):
    it = iter(xs)
    try:
        acc = next(it)
    except StopIteration:
        return NOTHING
    for x in it:
        acc = f(acc, x)
    return Some(acc)
```

Uses the first element as the initial accumulator. Returns `NOTHING` for empty collections, `Some(result)` otherwise.

### Examples

```python
from fptk.core.func import reduce
from fptk.adt.option import NOTHING

# Find maximum
reduce(max, [1, 5, 3])  # Some(5)

# Sum
reduce(lambda a, b: a + b, [1, 2, 3])  # Some(6)

# Empty collection
reduce(max, [])  # NOTHING

# Single element
reduce(max, [42])  # Some(42)

# Safe extraction
result = reduce(max, user_scores)
if result.is_some():
    print(f"Highest score: {result.unwrap()}")
else:
    print("No scores recorded")
```
