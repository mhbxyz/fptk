# State

`fptk.adt.state` provides the `State` monad for pure stateful computations. It lets you write code that reads and modifies state without actually mutating anything.

## Concept: The State Monad

The State monad represents computations that thread a mutable state through a sequence of operations, but purely—without actual mutation. Each operation receives the current state and returns a value plus the new state.

Think of it as: **a function that transforms state while producing a value**.

```python
State[S, A]  ≈  S -> (A, S)
```

A `State[Counter, int]` is a computation that, given a `Counter` state, produces an `int` value and a new `Counter` state.

### The Problem: Mutable State

```python
class Parser:
    def __init__(self, text):
        self.text = text
        self.pos = 0  # Mutable!

    def consume(self, n: int) -> str:
        result = self.text[self.pos:self.pos + n]
        self.pos += n  # Mutation!
        return result

    def peek(self) -> str:
        return self.text[self.pos]

# Hard to test: state is hidden and mutable
# Hard to reason about: what's the state at any point?
# Hard to backtrack: you'd need to save/restore pos
```

### The State Solution

```python
from fptk.adt.state import State, get, put, modify

@dataclass(frozen=True)
class ParserState:
    text: str
    pos: int

def consume(n: int) -> State[ParserState, str]:
    return (
        get()
        .bind(lambda s:
            put(ParserState(s.text, s.pos + n))
            .map(lambda _: s.text[s.pos:s.pos + n])
        )
    )

def peek() -> State[ParserState, str]:
    return get().map(lambda s: s.text[s.pos] if s.pos < len(s.text) else "")

# Pure, testable, composable
# Easy to backtrack: just keep the old state
initial = ParserState("hello", 0)
result, final_state = consume(3).run(initial)
# result = "hel", final_state = ParserState("hello", 3)
```

## API

### Types

| Type | Description |
|------|-------------|
| `State[S, A]` | Computation with state `S` producing value `A` |

### Constructor

```python
from fptk.adt.state import State

# Create from a function S -> (A, S)
state = State(lambda s: (s * 2, s + 1))
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `map(f)` | `(A -> B) -> State[S, B]` | Transform the result |
| `bind(f)` | `(A -> State[S, B]) -> State[S, B]` | Chain State-returning functions |
| `run(initial)` | `(S) -> (A, S)` | Execute with initial state |

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `get()` | `() -> State[S, S]` | Get the current state |
| `put(s)` | `(S) -> State[S, None]` | Replace the state |
| `modify(f)` | `(S -> S) -> State[S, None]` | Apply a function to the state |
| `gets(f)` | `(S -> A) -> State[S, A]` | Get and transform state |

## How It Works

### Data Structure

State wraps a function from state to (value, new_state):

```python
@dataclass(frozen=True, slots=True)
class State[S, A]:
    run_state: Callable[[S], tuple[A, S]]

    def run(self, initial_state: S) -> tuple[A, S]:
        return self.run_state(initial_state)
```

### The Functor: `map`

`map` transforms the value while preserving the state transition:

```python
def map(self, f):
    def run(state):
        value, new_state = self.run_state(state)
        return (f(value), new_state)
    return State(run)
```

### The Monad: `bind`

`bind` sequences state computations, threading state through:

```python
def bind(self, f):
    def run(state):
        value, intermediate_state = self.run_state(state)
        return f(value).run_state(intermediate_state)
    return State(run)
```

Key insight: the second computation receives the state *after* the first computation ran.

### State Primitives

```python
def get():
    """Return current state as the value, state unchanged."""
    return State(lambda s: (s, s))

def put(new_state):
    """Replace state with new_state, return None."""
    return State(lambda _: (None, new_state))

def modify(f):
    """Apply f to state, return None."""
    return State(lambda s: (None, f(s)))

def gets(f):
    """Return f(state), state unchanged."""
    return get().map(f)
```

## Examples

### Counter

```python
from fptk.adt.state import State, get, put, modify

# State is just an int
def increment() -> State[int, None]:
    return modify(lambda n: n + 1)

def decrement() -> State[int, None]:
    return modify(lambda n: n - 1)

def get_count() -> State[int, int]:
    return get()

# Compose operations
program = (
    increment()
    .bind(lambda _: increment())
    .bind(lambda _: increment())
    .bind(lambda _: get_count())
)

value, final_state = program.run(0)
# value = 3, final_state = 3
```

### Stack Operations

```python
from fptk.adt.state import State, get, put
from fptk.adt.option import Option, Some, NOTHING

Stack = tuple[int, ...]

def push(x: int) -> State[Stack, None]:
    return get().bind(lambda stack:
        put((x,) + stack)
    )

def pop() -> State[Stack, Option[int]]:
    def run(stack: Stack) -> tuple[Option[int], Stack]:
        if stack:
            return (Some(stack[0]), stack[1:])
        return (NOTHING, stack)
    return State(run)

def peek() -> State[Stack, Option[int]]:
    return get().map(lambda stack:
        Some(stack[0]) if stack else NOTHING
    )

# Use it
program = (
    push(1)
    .bind(lambda _: push(2))
    .bind(lambda _: push(3))
    .bind(lambda _: pop())
    .bind(lambda top:
        pop().map(lambda second: (top, second))
    )
)

result, final_stack = program.run(())
# result = (Some(3), Some(2)), final_stack = (1,)
```

### Random Number Generation

```python
from fptk.adt.state import State, get, put

# Linear congruential generator
@dataclass(frozen=True)
class RNG:
    seed: int

def next_int() -> State[RNG, int]:
    def run(rng: RNG) -> tuple[int, RNG]:
        # LCG parameters
        a, c, m = 1103515245, 12345, 2**31
        new_seed = (a * rng.seed + c) % m
        return (new_seed, RNG(new_seed))
    return State(run)

def random_range(lo: int, hi: int) -> State[RNG, int]:
    return next_int().map(lambda n: lo + (n % (hi - lo)))

# Generate multiple random numbers
def roll_dice(n: int) -> State[RNG, list[int]]:
    if n == 0:
        return State(lambda s: ([], s))
    return (
        random_range(1, 7)
        .bind(lambda die:
            roll_dice(n - 1).map(lambda rest: [die] + rest)
        )
    )

dice, final_rng = roll_dice(5).run(RNG(42))
# dice = [3, 1, 5, 2, 6] (deterministic given seed)
```

### Parser Combinator

```python
from fptk.adt.state import State, get, put, modify
from fptk.adt.result import Result, Ok, Err

@dataclass(frozen=True)
class ParseState:
    text: str
    pos: int

def parse_char(expected: str) -> State[ParseState, Result[str, str]]:
    def run(s: ParseState) -> tuple[Result[str, str], ParseState]:
        if s.pos >= len(s.text):
            return (Err("Unexpected end of input"), s)
        if s.text[s.pos] == expected:
            return (Ok(expected), ParseState(s.text, s.pos + 1))
        return (Err(f"Expected '{expected}', got '{s.text[s.pos]}'"), s)
    return State(run)

def parse_string(expected: str) -> State[ParseState, Result[str, str]]:
    if not expected:
        return State(lambda s: (Ok(""), s))
    return (
        parse_char(expected[0])
        .bind(lambda r: r.match(
            ok=lambda c: parse_string(expected[1:]).map(
                lambda r2: r2.map(lambda rest: c + rest)
            ),
            err=lambda e: State(lambda s: (Err(e), s))
        ))
    )

# Parse "hello"
result, final = parse_string("hello").run(ParseState("hello world", 0))
# result = Ok("hello"), final.pos = 5
```

### Game State

```python
@dataclass(frozen=True)
class GameState:
    player_hp: int
    enemy_hp: int
    turn: int

def damage_player(amount: int) -> State[GameState, None]:
    return modify(lambda g: GameState(
        g.player_hp - amount,
        g.enemy_hp,
        g.turn
    ))

def damage_enemy(amount: int) -> State[GameState, None]:
    return modify(lambda g: GameState(
        g.player_hp,
        g.enemy_hp - amount,
        g.turn
    ))

def next_turn() -> State[GameState, None]:
    return modify(lambda g: GameState(
        g.player_hp,
        g.enemy_hp,
        g.turn + 1
    ))

def is_game_over() -> State[GameState, bool]:
    return get().map(lambda g: g.player_hp <= 0 or g.enemy_hp <= 0)

# Combat round
def combat_round() -> State[GameState, str]:
    return (
        damage_enemy(10)  # Player attacks
        .bind(lambda _: is_game_over())
        .bind(lambda over:
            State(lambda s: ("Enemy defeated!", s)) if over
            else damage_player(5)  # Enemy attacks
                .bind(lambda _: next_turn())
                .bind(lambda _: is_game_over())
                .bind(lambda over2:
                    State(lambda s: ("Player defeated!", s)) if over2
                    else State(lambda s: ("Combat continues", s))
                )
        )
    )
```

## When to Use State

**Use State when:**

- You need to thread state through a computation purely
- You want testable state transformations
- You're building parsers, interpreters, or game logic
- You need to backtrack or branch with different states

**Don't use State when:**

- Simple cases where explicit parameters work fine
- Performance is critical (State adds function call overhead)
- The state is truly global and never needs rollback

## State vs Other Patterns

| Pattern | When to Use |
|---------|-------------|
| State monad | Pure state threading, composable, testable |
| Mutable objects | Performance-critical, simple cases |
| Reader | Read-only environment |
| Writer | Append-only log |

State is particularly useful for simulations, parsers, and any algorithm where you need to track intermediate state while maintaining referential transparency.

## See Also

- [`Reader`](reader.md) — Read-only environment access
- [`Writer`](writer.md) — Append-only logging
- [`Result`](result.md) — Combine with State for stateful fallible computations
