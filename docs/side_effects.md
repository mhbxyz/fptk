# Keeping Side Effects at the Edge: Layering with Result

Functional programming emphasizes purity: functions that are predictable, testable, and composable. Side effects—operations like I/O, mutations, or external interactions—complicate this by introducing unpredictability and dependencies. The principle of "keeping side effects at the edge" means structuring your code so that the core business logic remains pure, with side effects handled only at the boundaries of your application.

This guide explains how to apply this principle using fptk's ADTs, particularly by layering `Result` with other monads like `Reader`, `State`, and `Writer`. We'll explore why this matters, how to structure your code, and practical examples.

## Why Keep Side Effects at the Edge?

- **Testability**: Pure functions are easy to unit test without mocks or setup.
- **Composability**: Pure functions combine predictably; side effects don't.
- **Reasoning**: Pure code is easier to understand and debug.
- **Reusability**: Pure logic can be reused in different contexts (e.g., different environments or with different side effects).

Without this principle, side effects permeate your codebase, making it hard to reason about and maintain.

## Core Concept: Pure Core, Impure Edges

Structure your application as:

1. **Pure Core**: Business logic that takes inputs and produces outputs without side effects. Use ADTs like `Result`, `Reader`, `State`, and `Writer` to model computations purely.
2. **Impure Edges**: Thin layers that handle actual side effects (e.g., reading files, network calls, mutations), then feed pure inputs or consume pure outputs.

The edges "interpret" pure computations into the real world.

## Layering with Result

`Result[T, E]` models success/failure without exceptions. Layering it with other ADTs lets you handle errors while keeping other concerns (dependencies, state, logging) pure.

### Result + Reader: Dependency Injection with Error Handling

`Reader[R, A]` threads a read-only environment (e.g., config) through computations. Combine with `Result` for fallible computations that need config.

```python
from fptk.adt.reader import Reader, ask
from fptk.adt.result import Ok, Err, Result

@dataclass
class Config:
    api_url: str
    timeout: int

def fetch_user(user_id: int) -> Reader[Config, Result[dict, str]]:
    """Pure computation: fetch user data, may fail."""
    return ask().bind(lambda config: Reader(lambda _: Ok({"id": user_id, "name": "Alice"})))

def process_user(user_id: int) -> Reader[Config, Result[str, str]]:
    """Chain with error handling."""
    return fetch_user(user_id).bind(lambda result: result.map(lambda user: f"Processed {user['name']}").to_reader())

# Impure edge: actually perform I/O
async def impure_fetch(config: Config, user_id: int) -> Result[dict, str]:
    # Real I/O here (e.g., httpx call)
    # For demo, simulate success/failure
    if user_id > 0:
        return Ok({"id": user_id, "name": "Alice"})
    return Err("Invalid user ID")

# Pure core: describe the workflow
def workflow(user_id: int) -> Reader[Config, Result[str, str]]:
    return fetch_user(user_id).bind(lambda result: result.map(lambda user: f"Welcome {user['name']}").to_reader())

# Edge: run with real config and handle side effects
config = Config(api_url="https://api.example.com", api_key="secret")
result = workflow(1).run(config)
# Result[str, str] - pure until interpreted
```

To make `Result` work inside `Reader`, add a helper:

```python
class ResultReader[R, T, E]:
    def __init__(self, reader: Reader[R, Result[T, E]]):
        self.reader = reader

    def bind(self, f: Callable[[T], Reader[R, Result[U, E]]]) -> ResultReader[R, U, E]:
        return ResultReader(
            self.reader.bind(lambda result: result.match(
                lambda ok_val: f(ok_val),
                lambda err: Reader(lambda _: Err(err))
            ))
        )

    def run(self, env: R) -> Result[T, E]:
        return self.reader.run(env)
```

### Result + State: Stateful Computations with Error Handling

`State[S, A]` models pure state transitions. Layer with `Result` for stateful workflows that can fail.

```python
from fptk.adt.state import State, get, put, modify
from fptk.adt.result import Ok, Err, Result

def validate_and_update(balance: int, amount: int) -> State[int, Result[None, str]]:
    """Pure state update with validation."""
    return get().bind(lambda current: State(lambda _: (
        Ok(None) if current + amount >= 0 else Err("Insufficient funds"),
        current + amount
    )))

def transfer(from_id: int, to_id: int, amount: int) -> State[dict[int, int], Result[None, str]]:
    """Complex stateful workflow."""
    return get().bind(lambda accounts: State(lambda _: (
        Ok(None),  # Placeholder; real logic would update both accounts
        {**accounts, from_id: accounts[from_id] - amount, to_id: accounts[to_id] + amount}
    )))

# Impure edge: persist to database
def impure_persist(accounts: dict[int, int]) -> None:
    # Real mutation here (e.g., database update)
    pass

# Pure core: describe the transfer
def pure_transfer(from_id: int, to_id: int, amount: int) -> State[dict[int, int], Result[None, str]]:
    return transfer(from_id, to_id, amount)

# Edge: run and persist
initial_accounts = {1: 100, 2: 50}
result, final_accounts = pure_transfer(1, 2, 30).run(initial_accounts)
if result.is_ok():
    impure_persist(final_accounts)
```

### Result + Writer: Logged Computations with Error Handling

`Writer[W, A]` accumulates logs alongside values. Layer with `Result` for computations that log and may fail.

```python
from fptk.adt.writer import Writer, tell, monoid_list
from fptk.adt.result import Ok, Err, Result

def process_with_logging(data: str) -> Writer[list[str], Result[int, str]]:
    """Pure computation with logging."""
    return tell(["Starting processing"]).bind(lambda _: Writer.unit(
        Ok(len(data)) if data else Err("Empty data"),
        monoid_list
    ))

def complex_workflow(data: str) -> Writer[list[str], Result[str, str]]:
    """Chain logged, fallible steps."""
    return process_with_logging(data).bind(lambda result: result.match(
        lambda length: tell([f"Processed {length} chars"]).map(lambda _: Writer.unit(Ok(f"Result: {length}"), monoid_list)),
        lambda err: Writer.unit(Err(err), monoid_list)
    ))

# Impure edge: write logs to file
def impure_log_to_file(logs: list[str]) -> None:
    # Real I/O here
    pass

# Pure core: describe the workflow
def pure_workflow(data: str) -> Writer[list[str], Result[str, str]]:
    return complex_workflow(data)

# Edge: run and handle side effects
result, logs = pure_workflow("hello").run()
impure_log_to_file(logs)
# result is Result[str, str]
```

## Advanced Layering: Combining Multiple ADTs

You can stack multiple layers, e.g., `Reader[Config, State[AppState, Writer[Log, Result[A, E]]]]` for complex apps. This keeps everything pure until the edge.

```python
# Example: Config-dependent, stateful, logged computation that may fail
def complex_pure_workflow(input: str) -> Reader[Config, State[AppState, Writer[list[str], Result[str, str]]]]:
    # Implementation would chain Reader, State, Writer, and Result
    pass

# Edge: interpret into side effects
def impure_run_workflow(config: Config, initial_state: AppState, input: str) -> Result[str, str]:
    # Run the pure computation, then handle I/O based on logs/state
    pass
```

## Best Practices

- **Thin Edges**: Keep impure code minimal; delegate to pure functions.
- **Error Propagation**: Use `Result` to bubble errors up to the edge for handling.
- **Testing**: Test pure cores easily; mock edges if needed.
- **Composition**: Build complex workflows by composing simpler pure functions.
- **Performance**: Pure code is often easier to optimize and parallelize.

By layering `Result` with other ADTs and keeping side effects at the edge, you build robust, maintainable applications that are easy to reason about and test.