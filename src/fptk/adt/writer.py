"""Writer[W, A] — computations with monoidal log accumulation.

Use ``Writer`` when you want to accumulate logs or other monoidal values alongside
your computation results. It's perfect for tracing execution, collecting metrics,
or building audit trails without cluttering your core logic.

The ``Writer[W, A]`` monad represents computations that produce a value ``A``
alongside a log of type ``W``, where ``W`` is a monoid (has an identity element
and an associative combine operation). It's a pair ``(A, W)`` wrapped in a
monadic interface.

Everyday usage
- ``map(f)`` transforms the result while preserving the accumulated log.
- ``bind(f)`` chains computations that also produce logs; logs are combined
  using the monoid's combine operation.
- ``run()`` executes and returns (value, accumulated_log).
- ``tell(log)`` adds to the log without changing the value.
- ``listen()`` gets the current accumulated log alongside the value.
- ``censor(f)`` modifies the log without changing the value.

Interop and practicality
- You must provide a monoid instance for ``W`` (identity and combine functions).
- Writer composes well with ``Result`` for logged computations that can fail
  (e.g., ``Writer[Log, Result[A, E]]``).
- Use ``censor`` to filter or transform logs post-computation.
- Instances are immutable and hashable; equality compares the underlying pairs.
- Minimal overhead: just pair wrapping.

Quick examples

    >>> from fptk.adt.writer import Writer, tell, listen, censor
    >>> # Using list as monoid (concat)
    >>> w = Writer.unit(5, monoid_list).bind(lambda x: tell([f"got {x}"]).map(lambda _: x * 2))
    >>> w.run()
    (10, [5, 'got 5'])
    >>> listen(Writer.unit(3, monoid_list)).run()
    ((3, [3]), [3])
    >>> censor(lambda logs: [l.upper() for l in logs], tell(["hello"])).run()
    ((), ['HELLO'])
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

W = TypeVar("W")
A = TypeVar("A")
B = TypeVar("B")

__all__ = [
    "Writer",
    "tell",
    "listen",
    "censor",
    "Monoid",
    "monoid_list",
    "monoid_str",
    "monoid_sum",
    "monoid_product",
    "monoid_all",
    "monoid_any",
    "monoid_set",
    "monoid_max",
    "monoid_min",
]


@dataclass(frozen=True, slots=True)
class Monoid[W]:
    """A monoid with identity and combine operations."""

    identity: W
    combine: Callable[[W, W], W]


# Common monoids
monoid_list: Monoid[list[object]] = Monoid(identity=[], combine=lambda a, b: a + b)
monoid_str: Monoid[str] = Monoid(identity="", combine=lambda a, b: a + b)

# Numeric monoids
monoid_sum: Monoid[int | float] = Monoid(identity=0, combine=lambda a, b: a + b)
monoid_product: Monoid[int | float] = Monoid(identity=1, combine=lambda a, b: a * b)

# Boolean monoids
monoid_all: Monoid[bool] = Monoid(identity=True, combine=lambda a, b: a and b)
monoid_any: Monoid[bool] = Monoid(identity=False, combine=lambda a, b: a or b)

# Collection monoids
monoid_set: Monoid[frozenset[object]] = Monoid(identity=frozenset(), combine=lambda a, b: a | b)

# Numeric extrema
monoid_max: Monoid[float] = Monoid(identity=float("-inf"), combine=lambda a, b: max(a, b))
monoid_min: Monoid[float] = Monoid(identity=float("inf"), combine=lambda a, b: min(a, b))


@dataclass(frozen=True, slots=True)
class Writer[W, A]:
    """Computation that produces A alongside accumulated log W.

    Wraps a pair (A, W) with monadic operations.
    """

    value: A
    log: W
    monoid: Monoid[W]

    @classmethod
    def unit[B](cls, value: B, monoid: Monoid[W]) -> Writer[W, B]:
        """Create a Writer with value and monoid identity log."""
        return cls(value, monoid.identity, monoid)  # type: ignore[arg-type,return-value]

    def map[B](self: Writer[W, A], f: Callable[[A], B]) -> Writer[W, B]:
        """Transform the value with f, preserving the log."""
        return Writer(f(self.value), self.log, self.monoid)

    def bind[B](self: Writer[W, A], f: Callable[[A], Writer[W, B]]) -> Writer[W, B]:
        """Flat-map with f returning another Writer; combine logs."""
        wb = f(self.value)
        return Writer(wb.value, self.monoid.combine(self.log, wb.log), self.monoid)

    def run(self: Writer[W, A]) -> tuple[A, W]:
        """Execute and return (value, accumulated_log)."""
        return self.value, self.log

    def __repr__(self: Writer[W, A]) -> str:
        return f"Writer({self.value!r}, {self.log!r})"


def tell[W](log: W, monoid: Monoid[W]) -> Writer[W, None]:
    """Add to the log, returning unit value."""
    return Writer(None, log, monoid)


def listen[W, A](writer: Writer[W, A]) -> Writer[W, tuple[A, W]]:
    """Get the current value and accumulated log as a pair."""
    return Writer((writer.value, writer.log), writer.log, writer.monoid)


def censor[W, A](f: Callable[[W], W], writer: Writer[W, A]) -> Writer[W, A]:
    """Apply f to modify the log without changing the value."""
    return Writer(writer.value, f(writer.log), writer.monoid)
