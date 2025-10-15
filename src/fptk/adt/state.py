"""State[S, A] — pure stateful computations.

Use ``State`` when you need to model computations that read and write to some
mutable state without actually mutating anything. It's great for workflows that
need to track state changes purely, like parsers, game logic, or complex
transformations with intermediate state.

The ``State[S, A]`` monad represents computations that take an initial state
``S``, produce a value ``A``, and leave a final state ``S``. It's a function
``S -> (A, S)`` wrapped in a monadic interface.

Everyday usage
- ``map(f)`` transforms the result while preserving state transitions.
- ``bind(f)`` chains computations that can read/write state; state is threaded
  through automatically.
- ``run(initial_state)`` executes and returns (value, final_state).
- ``get()`` gets the current state as a State[S, S].
- ``put(new_state)`` sets the state to a new value, discarding the old.
- ``modify(f)`` applies a function to update the state.

Interop and practicality
- State composes well with ``Result`` for stateful computations that can fail
  (e.g., ``State[S, Result[A, E]]``).
- Use ``gets(f)`` to extract and transform the current state without changing it.
- Instances are immutable and hashable; equality compares the underlying functions.
- Minimal overhead: just function wrapping.

Quick examples

    >>> from fptk.adt.state import State, get, put, modify
    >>> s = get().map(lambda x: x + 1)
    >>> s.run(5)
    (6, 5)
    >>> put(10).bind(lambda _: get()).run(0)
    (10, 10)
    >>> modify(lambda x: x * 2).run(3)
    ((), 6)
    >>> get().bind(lambda x: modify(lambda _: x + 1)).run(2)
    ((), 3)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
    "State",
    "get",
    "put",
    "modify",
    "gets",
]


@dataclass(frozen=True, slots=True)
class State[S, A]:
    """Computation that reads/writes state S to produce A.

    Wraps a function S -> (A, S) with monadic operations.
    """

    run_state: Callable[[S], tuple[A, S]]

    def map[B](self: State[S, A], f: Callable[[A], B]) -> State[S, B]:
        """Transform the result with f, preserving state transitions."""
        return State(lambda state: (f(self.run_state(state)[0]), self.run_state(state)[1]))

    def bind[B](self: State[S, A], f: Callable[[A], State[S, B]]) -> State[S, B]:
        """Flat-map with f returning another State."""
        return State(lambda state: f(self.run_state(state)[0]).run_state(self.run_state(state)[1]))

    def run(self: State[S, A], initial_state: S) -> tuple[A, S]:
        """Execute the computation with initial state, returning (value, final_state)."""
        return self.run_state(initial_state)

    def __repr__(self: State[S, A]) -> str:
        return f"State({self.run_state!r})"


def get[S]() -> State[S, S]:
    """Get the current state as a State[S, S]."""
    return State(lambda state: (state, state))


def put[S](new_state: S) -> State[S, None]:
    """Set the state to new_state, returning unit."""
    return State(lambda _: (None, new_state))


def modify[S](f: Callable[[S], S]) -> State[S, None]:
    """Apply f to update the state, returning unit."""
    return State(lambda state: (None, f(state)))


def gets[S, A](f: Callable[[S], A]) -> State[S, A]:
    """Get and transform the current state without changing it."""
    return get().map(f)
