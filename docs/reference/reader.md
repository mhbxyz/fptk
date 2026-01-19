# Reader

`fptk.adt.reader` provides the `Reader` monad for dependency injection. It lets you write functions that depend on some environment (configuration, services, context) without explicitly passing that environment through every function call.

## Concept: The Reader Monad

The Reader monad represents computations that depend on a shared, read-only environment. Instead of passing configuration or dependencies through every function parameter, Reader threads it automatically.

Think of it as: **a function waiting for its environment**.

```python
Reader[R, A]  ≈  R -> A
```

A `Reader[Config, User]` is a computation that, given a `Config`, produces a `User`.

### The Problem: Dependency Threading

```python
def get_user(db: Database, cache: Cache, id: int) -> User:
    cached = cache.get(id)
    if cached:
        return cached
    user = db.query(id)
    cache.set(id, user)
    return user

def get_user_posts(db: Database, cache: Cache, user_id: int) -> list[Post]:
    user = get_user(db, cache, user_id)  # Must pass db, cache
    return db.query_posts(user.id)

def get_dashboard(db: Database, cache: Cache, user_id: int) -> Dashboard:
    user = get_user(db, cache, user_id)  # Pass again
    posts = get_user_posts(db, cache, user_id)  # And again
    return Dashboard(user, posts)
```

Every function must explicitly accept and pass `db` and `cache`. It's noisy and error-prone.

### The Reader Solution

```python
from fptk.adt.reader import Reader, ask

@dataclass
class Env:
    db: Database
    cache: Cache

def get_user(id: int) -> Reader[Env, User]:
    def run(env: Env) -> User:
        cached = env.cache.get(id)
        if cached:
            return cached
        user = env.db.query(id)
        env.cache.set(id, user)
        return user
    return Reader(run)

def get_user_posts(user_id: int) -> Reader[Env, list[Post]]:
    return get_user(user_id).bind(
        lambda user: ask().map(lambda env: env.db.query_posts(user.id))
    )

def get_dashboard(user_id: int) -> Reader[Env, Dashboard]:
    return (
        get_user(user_id)
        .bind(lambda user:
            get_user_posts(user_id).map(lambda posts:
                Dashboard(user, posts)
            )
        )
    )

# Run with actual dependencies
env = Env(db=real_db, cache=real_cache)
dashboard = get_dashboard(42).run(env)
```

Dependencies are injected once at the top. Functions compose without passing `env`.

## API

### Types

| Type | Description |
|------|-------------|
| `Reader[R, A]` | Computation needing environment `R` to produce `A` |

### Constructor

```python
from fptk.adt.reader import Reader

# Create from a function
reader = Reader(lambda env: env.config["timeout"])
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map(f)` | `(A -> B) -> Reader[R, B]` | Transform the result |
| `bind(f)` | `(A -> Reader[R, B]) -> Reader[R, B]` | Chain Reader-returning functions |
| `run(env)` | `(R) -> A` | Execute with environment |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `ask()` | `() -> Reader[R, R]` | Get the entire environment |
| `local(f, reader)` | `(R -> R, Reader[R, A]) -> Reader[R, A]` | Run with modified environment |

## How It Works

### Data Structure

Reader wraps a function from environment to value:

```python
@dataclass(frozen=True, slots=True)
class Reader[R, A]:
    run_reader: Callable[[R], A]

    def run(self, env: R) -> A:
        return self.run_reader(env)
```

### The Functor: `map`

`map` transforms the result while keeping the environment dependency:

```python
def map(self, f):
    return Reader(lambda env: f(self.run_reader(env)))
```

### The Monad: `bind`

`bind` chains computations that both depend on the environment:

```python
def bind(self, f):
    return Reader(lambda env: f(self.run_reader(env)).run_reader(env))
```

Key insight: the same `env` is passed to both the original Reader and the Reader returned by `f`.

### `ask`: Access the Environment

`ask()` creates a Reader that just returns the environment:

```python
def ask():
    return Reader(lambda env: env)
```

Use it when you need to access the environment in the middle of a chain:

```python
ask().map(lambda env: env.config["database_url"])
```

### `local`: Modify Environment Temporarily

`local` runs a Reader with a transformed environment:

```python
def local(f, reader):
    return Reader(lambda env: reader.run_reader(f(env)))
```

Useful for testing or scoped overrides:

```python
# Run with increased timeout
local(lambda env: env._replace(timeout=30), my_reader)
```

## Examples

### Configuration Access

```python
from fptk.adt.reader import Reader, ask
from dataclasses import dataclass

@dataclass
class Config:
    db_url: str
    timeout: int
    debug: bool

def get_timeout() -> Reader[Config, int]:
    return ask().map(lambda c: c.timeout)

def get_db_url() -> Reader[Config, str]:
    return ask().map(lambda c: c.db_url)

def connection_string() -> Reader[Config, str]:
    return (
        get_db_url()
        .bind(lambda url:
            get_timeout().map(lambda timeout:
                f"{url}?timeout={timeout}"
            )
        )
    )

# Run
config = Config(db_url="postgres://localhost", timeout=30, debug=True)
conn = connection_string().run(config)
# "postgres://localhost?timeout=30"
```

### Service Dependencies

```python
@dataclass
class Services:
    user_repo: UserRepository
    email_service: EmailService
    logger: Logger

def create_user(data: dict) -> Reader[Services, Result[User, str]]:
    def run(s: Services) -> Result[User, str]:
        user = User.from_dict(data)
        result = s.user_repo.save(user)
        if result.is_ok():
            s.email_service.send_welcome(user.email)
            s.logger.info(f"Created user {user.id}")
        return result
    return Reader(run)

def get_user_with_posts(id: int) -> Reader[Services, Option[UserWithPosts]]:
    return ask().map(lambda s:
        from_nullable(s.user_repo.find(id))
        .map(lambda user:
            UserWithPosts(user, s.post_repo.find_by_user(id))
        )
    )
```

### Testing with Mock Environment

```python
# Production
prod_services = Services(
    user_repo=PostgresUserRepo(),
    email_service=SendGridService(),
    logger=CloudLogger()
)
result = create_user(data).run(prod_services)

# Testing
test_services = Services(
    user_repo=InMemoryUserRepo(),
    email_service=MockEmailService(),
    logger=NullLogger()
)
result = create_user(data).run(test_services)
```

### Using `local` for Scoped Changes

```python
def with_debug(reader: Reader[Config, A]) -> Reader[Config, A]:
    """Run a reader with debug mode enabled."""
    return local(lambda c: dataclasses.replace(c, debug=True), reader)

def process_request(req: Request) -> Reader[Config, Response]:
    computation = ...  # some Reader

    # Enable debug for certain requests
    if req.headers.get("X-Debug"):
        return with_debug(computation)
    return computation
```

### Combining with Result

```python
def fetch_user(id: int) -> Reader[Services, Result[User, str]]:
    return ask().map(lambda s:
        try_catch(s.user_repo.find)(id)
        .map_err(lambda e: f"Database error: {e}")
        .bind(lambda user:
            Ok(user) if user else Err(f"User {id} not found")
        )
    )

def fetch_user_posts(user_id: int) -> Reader[Services, Result[list[Post], str]]:
    return (
        fetch_user(user_id)
        .bind(lambda result:
            result.match(
                ok=lambda user: ask().map(lambda s:
                    Ok(s.post_repo.find_by_user(user.id))
                ),
                err=lambda e: Reader(lambda _: Err(e))
            )
        )
    )
```

## When to Use Reader

**Use Reader when:**

- You have dependencies that many functions need
- You want testable code with injectable dependencies
- You're building a framework or library with configurable behavior
- You want to separate "what to do" from "what to do it with"

**Don't use Reader when:**

- You only have one or two functions that need the dependency
- The dependency is truly global and never changes
- Performance is critical (Reader adds function call overhead)

## Reader vs Other Patterns

| Pattern | When to Use |
|---------|-------------|
| Reader | Pure dependency injection, composable pipelines |
| Global variables | Never (usually) |
| Explicit parameters | Few functions, simple dependencies |
| Class with self | Object-oriented design |
| Dependency injection framework | Large applications with complex lifecycles |

Reader is particularly useful when you want the benefits of dependency injection while keeping your code purely functional and composable.

## See Also

- [`State`](state.md) — When you need to both read and write state
- [`Result`](result.md) — Combine with Reader for fallible computations
- [Side Effects](../guide/side-effects.md) — Pure cores with effects at the edges
