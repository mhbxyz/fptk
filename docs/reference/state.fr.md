# State

`fptk.adt.state` fournit la monade `State` pour des calculs à état purs. Elle vous permet d'écrire du code qui lit et modifie l'état sans réellement muter quoi que ce soit.

## Concept : La monade State

La monade State représente des calculs qui propagent un état mutable à travers une séquence d'opérations, mais de manière pure — sans mutation réelle. Chaque opération reçoit l'état courant et retourne une valeur plus le nouvel état.

Considérez-la comme : **une fonction qui transforme l'état tout en produisant une valeur**.

```python
State[S, A]  ≈  S -> (A, S)
```

Un `State[Counter, int]` est un calcul qui, étant donné un état `Counter`, produit une valeur `int` et un nouvel état `Counter`.

### Le problème : L'état mutable

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

### La solution State

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
| `State[S, A]` | Calcul avec état `S` produisant une valeur `A` |

### Constructeur

```python
from fptk.adt.state import State

# Create from a function S -> (A, S)
state = State(lambda s: (s * 2, s + 1))
```

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `map(f)` | `(A -> B) -> State[S, B]` | Transforme le résultat |
| `bind(f)` | `(A -> State[S, B]) -> State[S, B]` | Chaîne des fonctions retournant un State |
| `run(initial)` | `(S) -> (A, S)` | Exécute avec l'état initial |

### Fonctions

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `get()` | `() -> State[S, S]` | Obtient l'état courant |
| `put(s)` | `(S) -> State[S, None]` | Remplace l'état |
| `modify(f)` | `(S -> S) -> State[S, None]` | Applique une fonction à l'état |
| `gets(f)` | `(S -> A) -> State[S, A]` | Obtient et transforme l'état |

## Fonctionnement

### Structure de données

State encapsule une fonction de l'état vers (valeur, nouvel_état) :

```python
@dataclass(frozen=True, slots=True)
class State[S, A]:
    run_state: Callable[[S], tuple[A, S]]

    def run(self, initial_state: S) -> tuple[A, S]:
        return self.run_state(initial_state)
```

### Le Functor : `map`

`map` transforme la valeur tout en préservant la transition d'état :

```python
def map(self, f):
    def run(state):
        value, new_state = self.run_state(state)
        return (f(value), new_state)
    return State(run)
```

### La Monade : `bind`

`bind` séquence les calculs à état, propageant l'état à travers :

```python
def bind(self, f):
    def run(state):
        value, intermediate_state = self.run_state(state)
        return f(value).run_state(intermediate_state)
    return State(run)
```

Point clé : le second calcul reçoit l'état *après* l'exécution du premier calcul.

### Primitives d'état

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

## Exemples

### Compteur

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

### Opérations sur une pile

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

### Génération de nombres aléatoires

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

### Combinateur de parseur

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

### État de jeu

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

## Quand utiliser State

**Utilisez State lorsque :**

- Vous devez propager l'état à travers un calcul de manière pure
- Vous voulez des transformations d'état testables
- Vous construisez des parseurs, des interpréteurs ou de la logique de jeu
- Vous devez revenir en arrière ou brancher avec des états différents

**N'utilisez pas State lorsque :**

- Des cas simples où des paramètres explicites fonctionnent bien
- Les performances sont critiques (State ajoute une surcharge d'appel de fonction)
- L'état est vraiment global et n'a jamais besoin de retour en arrière

## State vs autres patterns

| Pattern | Quand l'utiliser |
|---------|------------------|
| Monade State | Propagation d'état pure, composable, testable |
| Objets mutables | Cas critiques en performance, cas simples |
| Reader | Environnement en lecture seule |
| Writer | Journal en ajout seul |

State est particulièrement utile pour les simulations, les parseurs, et tout algorithme où vous devez suivre l'état intermédiaire tout en maintenant la transparence référentielle.

## Voir aussi

- [`Reader`](reader.md) — Accès à l'environnement en lecture seule
- [`Writer`](writer.md) — Journalisation en ajout seul
- [`Result`](result.md) — Combiner avec State pour des calculs à état faillibles
