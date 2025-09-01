"""Option (Some/_None) — a lightweight optional type.

This module provides a tiny, typed alternative to using ``None`` directly. The
``Option[T]`` algebraic data type has two variants:

- ``Some(value)``: wraps a present value of type ``T``
- ``_None`` (singleton ``NONE``): represents the absence of a value

Core operations are ``map`` (transform the contained value), ``bind`` (monadic
flat-map), ``get_or`` (provide a default), and ``iter`` (iterate over zero-or-one
values). All variants are immutable and hashable.

Examples:

    >>> from fptk.adt.option import Some, NONE, from_nullable
    >>> Some(2).map(lambda x: x + 1).get_or(0)
    3
    >>> NONE.map(lambda x: x + 1).get_or(0)
    0
    >>> from_nullable("x").bind(lambda s: Some(s.upper())).get_or("-")
    'X'

Prefer constructing options explicitly via ``Some``/``NONE`` or ``from_nullable``
when turning ``T | None`` into ``Option[T]``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar, cast

__all__ = [
    "Option",
    "Some",
    "NONE",
    "from_nullable",
]

T = TypeVar("T")
U = TypeVar("U")


class Option[T]:
    """Optional value container with ``Some``/``_None`` variants.

    Instances are either ``Some[T]`` or the ``NONE`` singleton. Use the
    provided combinators to transform and consume values without branching.
    """

    def is_some(self) -> bool:
        """Return ``True`` if this is ``Some``.

        Subclasses implement this; calling on the base type is not expected.
        """
        raise NotImplementedError

    def is_none(self) -> bool:
        """Return ``True`` if this is ``NONE`` (i.e., not ``Some``)."""
        return not self.is_some()

    def map(self, f: Callable[[T], U]) -> Option[U]:
        """Apply ``f`` to the contained value if ``Some``; otherwise ``NONE``.

        Mapping preserves the optional nature: ``Some(x).map(f)`` becomes
        ``Some(f(x))``; ``NONE.map(f)`` stays ``NONE``.
        """
        return Some(f(self.value)) if isinstance(self, Some) else cast(Option[U], NONE)

    def bind(self, f: Callable[[T], Option[U]]) -> Option[U]:
        """Flat-map with ``f`` returning another ``Option``.

        Also known as ``and_then``/``flat_map``.
        """
        return f(self.value) if isinstance(self, Some) else cast(Option[U], NONE)

    def get_or(self, default: U) -> T | U:
        """Unwrap the value or return ``default`` if ``NONE``."""
        return self.value if isinstance(self, Some) else default

    def iter(self) -> Iterator[T]:
        """Iterate over zero-or-one items (``Some`` yields one element)."""
        if isinstance(self, Some):
            yield self.value


@dataclass(frozen=True, slots=True)
class Some[T](Option[T]):
    value: T

    def is_some(self) -> bool:
        """``Some`` always reports presence of a value."""
        return True


@dataclass(frozen=True, slots=True)
class _None(Option[None]):
    def is_some(self) -> bool:
        """``_None`` always reports absence of a value."""
        return False


NONE = _None()


def from_nullable[T](x: T | None) -> Option[T]:
    """Convert a ``T | None`` into ``Option[T]``.

    Returns ``Some(x)`` when ``x`` is not ``None``; otherwise ``NONE``.
    """
    return cast(Option[T], NONE) if x is None else Some(x)
