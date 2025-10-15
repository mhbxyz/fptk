"""Non-empty list (NonEmptyList) — a list with at least one element.

This minimal ADT guarantees non-emptiness by construction with a ``head`` and
an optional ``tail`` tuple. It supports iteration in order, ``append`` to add an
element at the end, and a ``from_iter`` constructor that returns ``None`` for an
empty input iterable.

Examples:

    >>> from fptk.adt.nelist import NonEmptyList
    >>> nel = NonEmptyList(1).append(2).append(3)
    >>> list(nel)
    [1, 2, 3]
    >>> NonEmptyList.from_iter(["a", "b"]).head
    'a'
    >>> NonEmptyList.from_iter([]) is None
    True
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

__all__ = [
    "NonEmptyList",
]


@dataclass(frozen=True, slots=True)
class NonEmptyList[E]:
    """A simple, immutable non-empty list with ``head`` and ``tail``.

    - ``head``: first element (guarantees non-emptiness)
    - ``tail``: zero-or-more remaining elements stored as a tuple
    """

    head: E
    tail: tuple[E, ...] = ()

    def __iter__(self: NonEmptyList[E]) -> Iterator[E]:
        """Iterate from ``head`` through all elements in ``tail``."""
        yield self.head
        yield from self.tail

    def append(self: NonEmptyList[E], e: E) -> NonEmptyList[E]:
        """Return a new list with ``e`` appended at the end."""
        return NonEmptyList(self.head, self.tail + (e,))

    @staticmethod
    def from_iter(it: Iterable[E]) -> NonEmptyList[E] | None:
        """Build a ``NonEmptyList`` from an iterable, or ``None`` if empty."""
        iterator = iter(it)
        try:
            h = next(iterator)
        except StopIteration:
            return None
        return NonEmptyList(h, tuple(iterator))

    def to_list(self: NonEmptyList[E]) -> list[E]:
        """Convert to a regular Python list."""
        return list(self)
