"""Option (Some/_None) — a lightweight optional type.

Use ``Option`` when you want to make absence explicit instead of sprinkling
``if x is None`` throughout your code. It shines at boundaries (parsing, lookups,
config) and when composing transformations that may drop out early.

The ``Option[T]`` algebraic data type has two variants:

- ``Some(value)``: wraps a present value of type ``T``
- ``_None`` (singleton ``NONE``): represents the absence of a value

Everyday usage
- ``map(f)`` transforms the value if present; otherwise does nothing.
- ``bind(f)`` (aka ``and_then``) chains computations that themselves return
  ``Option``; the first ``NONE`` short-circuits the chain.
- ``get_or(default)`` unwraps with a fallback; ``or_else`` picks an alternative
  ``Option`` (eager value or lazy thunk).
- ``match(some, none)`` and ``iter()`` are simple ways to consume values.
- ``to_result(err)`` turns missing values into typed errors for richer flows.

Interop and practicality
- ``Option`` pairs well with ``traverse`` helpers to work over collections.
- Objects are immutable and hashable; equality is by contained value/variant.
- No magic: these are tiny wrappers around explicit branching. There is minor
  call overhead; avoid deep chains in hot loops.

Quick examples

    >>> from fptk.adt.option import Some, NONE, from_nullable
    >>> Some(2).map(lambda x: x + 1).get_or(0)
    3
    >>> NONE.map(lambda x: x + 1).get_or(0)
    0
    >>> from_nullable("x").bind(lambda s: Some(s.upper())).get_or("-")
    'X'
    >>> NONE.or_else(lambda: Some(9))
    Some(9)
    >>> Some(2).to_result("e").is_ok()
    True
    >>> NONE.match(lambda x: x, lambda: "-")
    '-'

Prefer constructing options explicitly via ``Some``/``NONE`` or ``from_nullable``
when turning ``T | None`` into ``Option[T]``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar, cast

from fptk.adt.result import Err, Ok, Result

__all__ = [
    "Option",
    "Some",
    "NONE",
    "from_nullable",
]

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


class Option[T]:
    """Optional value container with ``Some``/``_None`` variants.

    Instances are either ``Some[T]`` or the ``NONE`` singleton. Use the
    provided combinators to transform and consume values without branching.
    """

    def is_some(self: Option[T]) -> bool:
        """Return ``True`` if this is ``Some``.

        Subclasses implement this; calling on the base type is not expected.
        """
        raise NotImplementedError

    def is_none(self: Option[T]) -> bool:
        """Return ``True`` if this is ``NONE`` (i.e., not ``Some``)."""
        return not self.is_some()

    def map(self: Option[T], f: Callable[[T], U]) -> Option[U]:
        """Apply ``f`` to the contained value if ``Some``; otherwise ``NONE``.

        Mapping preserves the optional nature: ``Some(x).map(f)`` becomes
        ``Some(f(x))``; ``NONE.map(f)`` stays ``NONE``.
        """
        return Some(f(self.value)) if isinstance(self, Some) else cast(Option[U], NONE)

    def bind(self: Option[T], f: Callable[[T], Option[U]]) -> Option[U]:
        """Flat-map with ``f`` returning another ``Option``.

        Also known as ``and_then``/``flat_map``.
        """
        return f(self.value) if isinstance(self, Some) else cast(Option[U], NONE)

    def get_or(self: Option[T], default: U) -> T | U:
        """Unwrap the value or return ``default`` if ``NONE``."""
        return self.value if isinstance(self, Some) else default

    def iter(self: Option[T]) -> Iterator[T]:
        """Iterate over zero-or-one items (``Some`` yields one element)."""
        if isinstance(self, Some):
            yield self.value

    def or_else(self: Option[T], alt: Option[T] | Callable[[], Option[T]]) -> Option[T]:
        """Return self if Some; otherwise the alternative Option (value or thunk)."""
        if isinstance(self, Some):
            return self
        return alt() if callable(alt) else alt

    def to_result(self: Option[T], err: E | Callable[[], E]) -> Result[T, E]:
        """Convert Option[T] to Result[T, E] (Some -> Ok; NONE -> Err(err))."""
        if isinstance(self, Some):
            return Ok(self.value)
        return Err(err()) if callable(err) else Err(err)

    def match(self: Option[T], some: Callable[[T], U], none: Callable[[], U]) -> U:
        """Pattern-match helper."""
        return some(self.value) if isinstance(self, Some) else none()


@dataclass(frozen=True, slots=True)
class Some[T](Option[T]):
    value: T

    def is_some(self: Some[T]) -> bool:
        """``Some`` always reports presence of a value."""
        return True

    def __repr__(self: Some[T]) -> str:  # nicer than dataclass default
        return f"Some({self.value!r})"


@dataclass(frozen=True, slots=True)
class _None(Option[None]):
    def is_some(self: _None) -> bool:
        """``_None`` always reports absence of a value."""
        return False

    def __repr__(self: _None) -> str:
        return "NONE"


NONE = _None()


def from_nullable[T](x: T | None) -> Option[T]:
    """Convert a ``T | None`` into ``Option[T]``.

    Returns ``Some(x)`` when ``x`` is not ``None``; otherwise ``NONE``.
    """
    return cast(Option[T], NONE) if x is None else Some(x)
