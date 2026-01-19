# Side Effects at the Edge

Functional programming emphasizes purity: functions that are predictable, testable, and composable. Side effects—operations like I/O, mutations, or external interactions—complicate this by introducing unpredictability and dependencies.

The principle of "keeping side effects at the edge" means structuring your code so that the core business logic remains pure, with side effects handled only at the boundaries of your application.

## Why Keep Side Effects at the Edge?

- **Testability**: Pure functions are easy to unit test without mocks or setup
- **Composability**: Pure functions combine predictably; side effects don't
- **Reasoning**: Pure code is easier to understand and debug
- **Reusability**: Pure logic can be reused in different contexts

Without this principle, side effects permeate your codebase, making it hard to reason about and maintain.

## Pure Core, Impure Edges

Structure your application as:

1. **Pure Core**: Business logic that takes inputs and produces outputs without side effects. Use ADTs like `Result`, `Reader`, `State`, and `Writer` to model computations purely.
2. **Impure Edges**: Thin layers that handle actual side effects (reading files, network calls, mutations), then feed pure inputs or consume pure outputs.

The edges "interpret" pure computations into the real world.

## Layering with Result

`Result[T, E]` models success/failure without exceptions. Layering it with other ADTs lets you handle errors while keeping other concerns (dependencies, state, logging) pure.

### Result + Reader: Dependency Injection with Error Handling

`Reader[R, A]` threads a read-only environment (e.g., config) through computations. Combine with `Result` for fallible computations that need config.

```python
from dataclasses import dataclass
from fptk.adt.reader import Reader, ask
from fptk.adt.result import Ok, Err, Result

@dataclass
class Config:
    api_url: str
    timeout: int

def fetch_user(user_id: int) -> Reader[Config, Result[dict, str]]:
    """Pure computation: describe fetching user data."""
    def run(config: Config) -> Result[dict, str]:
        if user_id <= 0:
            return Err("Invalid user ID")
        # In pure core, we just describe what to do
        return Ok({"id": user_id, "url": config.api_url})
    return Reader(run)

def process_user(user_id: int) -> Reader[Config, Result[str, str]]:
    """Chain with error handling."""
    return fetch_user(user_id).map(
        lambda result: result.map(lambda user: f"Processed user {user['id']}")
    )

# Pure core: describe the workflow
config = Config(api_url="https://api.example.com", timeout=30)

# Edge: run with real config
result = process_user(1).run(config)
# Ok("Processed user 1")

result = process_user(-1).run(config)
# Err("Invalid user ID")
```

### Result + State: Stateful Computations with Error Handling

`State[S, A]` models pure state transitions. Layer with `Result` for stateful workflows that can fail.

```python
from fptk.adt.state import State, get, modify
from fptk.adt.result import Ok, Err, Result

def withdraw(amount: int) -> State[int, Result[int, str]]:
    """Pure state update with validation."""
    def run(balance: int) -> tuple[Result[int, str], int]:
        if amount > balance:
            return Err("Insufficient funds"), balance
        new_balance = balance - amount
        return Ok(new_balance), new_balance
    return State(run)

def transfer(amount: int) -> State[int, Result[str, str]]:
    """Chain stateful operations."""
    return withdraw(amount).map(
        lambda result: result.map(lambda bal: f"New balance: {bal}")
    )

# Pure core: describe the transfer
initial_balance = 100

# Edge: run and get final state
result, final_balance = transfer(30).run(initial_balance)
# result = Ok("New balance: 70"), final_balance = 70

result, final_balance = transfer(150).run(initial_balance)
# result = Err("Insufficient funds"), final_balance = 100
```

### Result + Writer: Logged Computations with Error Handling

`Writer[W, A]` accumulates logs alongside values. Layer with `Result` for computations that log and may fail.

```python
from fptk.adt.writer import Writer, tell, monoid_list
from fptk.adt.result import Ok, Err, Result

def process_data(data: str) -> Writer[list[str], Result[int, str]]:
    """Pure computation with logging."""
    if not data:
        return Writer((Err("Empty data"), ["Error: empty input"]))

    return (
        tell(["Starting processing"])
        .bind(lambda _: tell([f"Processing {len(data)} chars"]))
        .map(lambda _: Ok(len(data)))
    )

# Edge: run and handle side effects
result, logs = process_data("hello world").run()
# result = Ok(11)
# logs = ["Starting processing", "Processing 11 chars"]

result, logs = process_data("").run()
# result = Err("Empty data")
# logs = ["Error: empty input"]

# Impure edge: write logs to file
def persist_logs(logs: list[str]) -> None:
    with open("app.log", "a") as f:
        for log in logs:
            f.write(log + "\n")
```

## Best Practices

| Practice | Description |
|----------|-------------|
| **Thin Edges** | Keep impure code minimal; delegate to pure functions |
| **Error Propagation** | Use `Result` to bubble errors up to the edge for handling |
| **Testing** | Test pure cores easily; mock edges only if needed |
| **Composition** | Build complex workflows by composing simpler pure functions |

## Example: Complete Workflow

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.adt.reader import Reader, ask

@dataclass
class AppConfig:
    db_url: str
    api_key: str

# Pure core: describe business logic
def validate_user(data: dict) -> Result[dict, str]:
    if not data.get("email"):
        return Err("Email required")
    return Ok(data)

def create_user_workflow(data: dict) -> Reader[AppConfig, Result[dict, str]]:
    """Pure workflow: validation -> save -> notify"""
    return ask().map(lambda config:
        validate_user(data)
        .map(lambda user: {**user, "db": config.db_url})
    )

# Impure edge: run with real config and perform I/O
def run_create_user(data: dict) -> Result[dict, str]:
    config = AppConfig(db_url="postgres://...", api_key="secret")
    result = create_user_workflow(data).run(config)

    # Handle side effects based on result
    if result.is_ok():
        user = result.unwrap()
        save_to_database(user)  # Impure
        send_email(user)        # Impure

    return result
```

By layering `Result` with other ADTs and keeping side effects at the edge, you build robust, maintainable applications that are easy to reason about and test.
