# API Reference

## fptk.core.func

Function combinators and utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `pipe` | `(x, *fns) -> T` | Thread value through functions |
| `compose` | `(f, g) -> fn` | Compose two functions: `f(g(x))` |
| `curry` | `(fn) -> fn` | Curry a function |
| `flip` | `(fn) -> fn` | Swap first two arguments |
| `tap` | `(fn) -> fn` | Run side effect, return input |
| `thunk` | `(fn) -> fn` | Lazy memoized value |
| `identity` | `(x) -> x` | Return input unchanged |
| `const` | `(x) -> fn` | Always return `x` |
| `once` | `(fn) -> fn` | Run once, memoize result |
| `try_catch` | `(fn) -> fn` | Convert exceptions to `Result` |
| `async_pipe` | `async (x, *fns) -> T` | Async version of `pipe` |

---

## fptk.adt.option

Optional values.

### Types

| Type | Description |
|------|-------------|
| `Option[T]` | Base type for optional values |
| `Some[T]` | Present value |
| `Nothing` | Absent value (class) |
| `NOTHING` | Singleton instance of `Nothing` |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `from_nullable` | `(x: T \| None) -> Option[T]` | Convert nullable to Option |

### Option Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_some` | `() -> bool` | Check if Some |
| `is_none` | `() -> bool` | Check if Nothing |
| `map` | `(fn) -> Option[U]` | Transform value if present |
| `bind` | `(fn) -> Option[U]` | Chain Option-returning function |
| `map_async` | `async (fn) -> Option[U]` | Async map |
| `bind_async` | `async (fn) -> Option[U]` | Async bind |
| `unwrap_or` | `(default) -> T` | Get value or default |
| `or_else` | `(fn) -> Option[T]` | Alternative if Nothing |
| `to_result` | `(err) -> Result[T, E]` | Convert to Result |
| `match` | `(some, none) -> U` | Pattern match |
| `unwrap` | `() -> T` | Get value or raise |
| `expect` | `(msg) -> T` | Get value or raise with message |

---

## fptk.adt.result

Success or failure with typed error.

### Types

| Type | Description |
|------|-------------|
| `Result[T, E]` | Base type for success/failure |
| `Ok[T, E]` | Success variant |
| `Err[T, E]` | Failure variant |

### Result Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_ok` | `() -> bool` | Check if Ok |
| `is_err` | `() -> bool` | Check if Err |
| `map` | `(fn) -> Result[U, E]` | Transform success value |
| `bind` | `(fn) -> Result[U, E]` | Chain Result-returning function |
| `map_async` | `async (fn) -> Result[U, E]` | Async map |
| `bind_async` | `async (fn) -> Result[U, E]` | Async bind |
| `map_err` | `(fn) -> Result[T, F]` | Transform error |
| `unwrap_or` | `(default) -> T` | Get value or default |
| `unwrap_or_else` | `(fn) -> T` | Get value or compute default |
| `match` | `(ok, err) -> U` | Pattern match |
| `unwrap` | `() -> T` | Get value or raise |
| `expect` | `(msg) -> T` | Get value or raise with message |

---

## fptk.adt.nelist

Non-empty list.

### Types

| Type | Description |
|------|-------------|
| `NonEmptyList[E]` | List with at least one element |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `head` | `E` | First element |
| `tail` | `tuple[E, ...]` | Remaining elements |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `append` | `(e) -> NonEmptyList[E]` | Add element at end |
| `from_iter` | `(it) -> Option[NonEmptyList[E]]` | Create from iterable |
| `to_list` | `() -> list[E]` | Convert to list |
| `__iter__` | `() -> Iterator[E]` | Iterate all elements |

---

## fptk.adt.reader

Dependency injection monad.

### Types

| Type | Description |
|------|-------------|
| `Reader[R, A]` | Computation requiring environment `R` to produce `A` |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `ask` | `() -> Reader[R, R]` | Get the environment |
| `local` | `(fn, reader) -> Reader[R, A]` | Run with modified environment |

### Reader Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map` | `(fn) -> Reader[R, B]` | Transform result |
| `bind` | `(fn) -> Reader[R, B]` | Chain Reader-returning function |
| `run` | `(env) -> A` | Execute with environment |

---

## fptk.adt.state

Pure stateful computations.

### Types

| Type | Description |
|------|-------------|
| `State[S, A]` | Computation with state `S` producing `A` |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `get` | `() -> State[S, S]` | Get current state |
| `put` | `(s) -> State[S, None]` | Set state |
| `modify` | `(fn) -> State[S, None]` | Modify state with function |
| `gets` | `(fn) -> State[S, A]` | Get and transform state |

### State Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map` | `(fn) -> State[S, B]` | Transform result |
| `bind` | `(fn) -> State[S, B]` | Chain State-returning function |
| `run` | `(s) -> (A, S)` | Execute with initial state |

---

## fptk.adt.writer

Log accumulation monad.

### Types

| Type | Description |
|------|-------------|
| `Writer[W, A]` | Computation producing `A` with log `W` |
| `Monoid[W]` | Protocol for combinable values |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `tell` | `(w) -> Writer[W, None]` | Write to log |
| `listen` | `(writer) -> Writer[W, (A, W)]` | Get value and log |
| `censor` | `(fn, writer) -> Writer[W, A]` | Modify log |
| `monoid_list` | `Monoid[list]` | List concatenation monoid |
| `monoid_str` | `Monoid[str]` | String concatenation monoid |

### Writer Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `unit` | `(a, monoid) -> Writer[W, A]` | Create with empty log |
| `map` | `(fn) -> Writer[W, B]` | Transform result |
| `bind` | `(fn) -> Writer[W, B]` | Chain Writer-returning function |
| `run` | `() -> (A, W)` | Execute and get result with log |

---

## fptk.adt.traverse

Sequence and traverse operations.

| Function | Signature | Description |
|----------|-----------|-------------|
| `sequence_option` | `(xs) -> Option[list]` | Collect Some values |
| `traverse_option` | `(xs, fn) -> Option[list]` | Map and collect Some |
| `sequence_result` | `(xs) -> Result[list, E]` | Collect Ok values |
| `traverse_result` | `(xs, fn) -> Result[list, E]` | Map and collect Ok |
| `traverse_option_async` | `async (xs, fn) -> Option[list]` | Async traverse Option |
| `traverse_result_async` | `async (xs, fn) -> Result[list, E]` | Async traverse Result |

---

## fptk.iter.lazy

Lazy iterator utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `map_iter` | `(fn, xs) -> Iterator` | Lazy map |
| `filter_iter` | `(pred, xs) -> Iterator` | Lazy filter |
| `chunk` | `(xs, n) -> Iterator[tuple]` | Split into chunks of size n |
| `group_by_key` | `(xs, key) -> Iterator` | Group consecutive by key |

---

## fptk.validate

Applicative validation.

| Function | Signature | Description |
|----------|-----------|-------------|
| `validate_all` | `(checks, value) -> Result[T, NonEmptyList[E]]` | Run all checks, accumulate errors |

---

## fptk.async_tools

Async utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `async_pipe` | `async (x, *fns) -> T` | Async pipe |
| `gather_results` | `async (tasks) -> Result[list, E]` | Gather Results, fail-fast |
| `gather_results_accumulate` | `async (tasks) -> Result[list, list[E]]` | Gather Results, accumulate errors |
