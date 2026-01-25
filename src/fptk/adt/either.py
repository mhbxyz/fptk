"""Either[L, R] — symmetric sum type for two alternatives.

Use ``Either`` when you need to represent one of two possible types without
the success/error semantics of ``Result``. It's perfect for branching logic
where both sides are equally valid outcomes.

The ``Either[L, R]`` algebraic data type represents values that can be:

- ``Left(value)``: left variant wrapping a value of type ``L``
- ``Right(value)``: right variant wrapping a value of type ``R``

Unlike ``Result``, there's no implied "success" or "failure" — both variants
are neutral alternatives.

Everyday usage
- ``map_left(f)`` transforms the left value; right passes through.
- ``map_right(f)`` transforms the right value; left passes through.
- ``bimap(f, g)`` transforms both sides at once.
- ``fold(on_left, on_right)`` pattern matches to produce a single result.
- ``swap()`` flips Left ↔ Right.
- ``is_left`` / ``is_right`` predicates for checking the variant.

Interop and practicality
- Use ``Either`` when both alternatives are valid (e.g., parse as int or keep as string).
- Use ``Result`` when you have clear success/failure semantics.
- Instances are immutable and hashable; equality compares contained values.

Quick examples

    >>> from fptk.adt.either import Left, Right
    >>> Left(42).map_left(lambda x: x * 2)
    Left(84)
    >>> Right("hello").map_right(str.upper)
    Right('HELLO')
    >>> Left(1).bimap(lambda x: x + 1, str.upper)
    Left(2)
    >>> Right("a").bimap(lambda x: x + 1, str.upper)
    Right('A')
    >>> Left(10).fold(lambda x: x * 2, lambda s: len(s))
    20
    >>> Left(1).swap()
    Right(1)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

__all__ = [
    "Either",
    "Left",
    "Right",
]


class Either[L, R]:
    """Value that is either Left[L] or Right[R]."""

    def is_left(self: Either[L, R]) -> bool:
        """Return ``True`` if this is ``Left``."""
        return isinstance(self, Left)

    def is_right(self: Either[L, R]) -> bool:
        """Return ``True`` if this is ``Right``."""
        return isinstance(self, Right)

    def map_left[L2](self: Either[L, R], f: Callable[[L], L2]) -> Either[L2, R]:
        """Transform the left value with ``f``; right passes through."""
        if isinstance(self, Left):
            return Left(f(self.value))
        return cast(Either[L2, R], self)

    def map_right[R2](self: Either[L, R], f: Callable[[R], R2]) -> Either[L, R2]:
        """Transform the right value with ``f``; left passes through."""
        if isinstance(self, Right):
            return Right(f(self.value))
        return cast(Either[L, R2], self)

    def bimap[L2, R2](
        self: Either[L, R],
        f: Callable[[L], L2],
        g: Callable[[R], R2],
    ) -> Either[L2, R2]:
        """Transform both sides: ``f`` for Left, ``g`` for Right."""
        if isinstance(self, Left):
            return Left(f(self.value))
        return Right(g(cast(Right[L, R], self).value))

    def fold[T](
        self: Either[L, R],
        on_left: Callable[[L], T],
        on_right: Callable[[R], T],
    ) -> T:
        """Pattern match: apply ``on_left`` or ``on_right`` based on variant."""
        if isinstance(self, Left):
            return on_left(self.value)
        return on_right(cast(Right[L, R], self).value)

    def swap(self: Either[L, R]) -> Either[R, L]:
        """Flip Left ↔ Right."""
        if isinstance(self, Left):
            return Right(self.value)
        return Left(cast(Right[L, R], self).value)

    def __repr__(self: Either[L, R]) -> str:
        if isinstance(self, Left):
            return f"Left({self.value!r})"
        return f"Right({cast(Right[L, R], self).value!r})"


@dataclass(frozen=True, slots=True, repr=False)
class Left[L, R](Either[L, R]):
    """Left variant of Either."""

    value: L


@dataclass(frozen=True, slots=True, repr=False)
class Right[L, R](Either[L, R]):
    """Right variant of Either."""

    value: R
