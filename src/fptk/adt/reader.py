"""Reader[R, A] — dependency injection via environment threading.

Use ``Reader`` when you want to thread a read-only environment (like config or
dependencies) through a computation without passing it explicitly. It shines for
dependency injection, configuration loading, and keeping functions pure while
accessing shared context.

The ``Reader[R, A]`` monad represents computations that depend on an environment
of type ``R`` and produce a value of type ``A``. It's essentially a function
``R -> A`` wrapped in a monadic interface.

Everyday usage
- ``map(f)`` transforms the result while preserving the environment dependency.
- ``bind(f)`` chains computations that themselves depend on the environment;
  the environment is threaded through automatically.
- ``run(env)`` executes the computation with a concrete environment value.
- ``ask()`` gets the current environment as a Reader.
- ``local(f)`` modifies the environment for a subcomputation.

Interop and practicality
- Reader composes well with ``Result`` for fallible computations that also
  need config (e.g., ``Reader[Config, Result[A, E]]``).
- Use ``local`` to temporarily modify the environment (e.g., for testing or
  scoped overrides).
- Instances are immutable and hashable; equality compares the underlying functions.
- Minimal overhead: just function wrapping.

Quick examples

    >>> from fptk.adt.reader import Reader, ask, local
    >>> r = ask().map(lambda env: env + 1)
    >>> r.run(5)
    6
    >>> r.bind(lambda x: ask().map(lambda env: x + env)).run(3)
    9
    >>> local(lambda env: env * 2, ask()).run(4)
    8
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
    "Reader",
    "ask",
    "local",
]


@dataclass(frozen=True, slots=True)
class Reader[R, A]:
    """Computation that depends on an environment R to produce A.

    Wraps a function R -> A with monadic operations.
    """

    run_reader: Callable[[R], A]

    def map[B](self: Reader[R, A], f: Callable[[A], B]) -> Reader[R, B]:
        """Transform the result with f, preserving environment dependency."""
        return Reader(lambda env: f(self.run_reader(env)))

    def bind[B](self: Reader[R, A], f: Callable[[A], Reader[R, B]]) -> Reader[R, B]:
        """Flat-map with f returning another Reader."""
        return Reader(lambda env: f(self.run_reader(env)).run_reader(env))

    def run(self: Reader[R, A], env: R) -> A:
        """Execute the computation with the given environment."""
        return self.run_reader(env)

    def __repr__(self: Reader[R, A]) -> str:
        return f"Reader({self.run_reader!r})"


def ask[R]() -> Reader[R, R]:
    """Get the current environment as a Reader[R, R]."""
    return Reader(lambda env: env)


def local[R, A](f: Callable[[R], R], reader: Reader[R, A]) -> Reader[R, A]:
    """Run a Reader in a locally modified environment."""
    return Reader(lambda env: reader.run_reader(f(env)))
