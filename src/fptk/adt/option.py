"""Option (Some/Nothing) — a lightweight optional type.

Use ``Option`` when you want to make absence explicit instead of sprinkling
``if x is None`` throughout your code. It shines at boundaries (parsing, lookups,
config) and when composing transformations that may drop out early.

The ``Option[T]`` algebraic data type has two variants:

- ``Some(value)``: wraps a present value of type ``T``
- ``Nothing`` (singleton ``NOTHING``): represents the absence of a value

Everyday usage
- ``map(f)`` transforms the value if present; otherwise does nothing.
- ``bind(f)`` (aka ``and_then``) chains computations that themselves return
  ``Option``; the first ``NOTHING`` short-circuits the chain.
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

    >>> from fptk.adt.option import Some, NOTHING, from_nullable
    >>> Some(2).map(lambda x: x + 1).get_or(0)
    3
    >>> NOTHING.map(lambda x: x + 1).get_or(0)
    0
    >>> from_nullable("x").bind(lambda s: Some(s.upper())).get_or("-")
    'X'
    >>> NOTHING.or_else(lambda: Some(9))
    Some(9)
    >>> Some(2).to_result("e").is_ok()
    True
    >>> NOTHING.match(lambda x: x, lambda: "-")
    '-'

Prefer constructing options explicitly via ``Some``/``NOTHING`` or ``from_nullable``
when turning ``T | None`` into ``Option[T]``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from typing import cast

from fptk.adt.result import Err, Ok, Result

__all__ = [
    "Option",
    "Some",
    "Nothing",
    "NOTHING",
    "from_nullable",
]


class Option[T]:
    """Optional value container with ``Some``/``Nothing`` variants.

    Instances are either ``Some[T]`` or the ``NOTHING`` singleton. Use the
    provided combinators to transform and consume values without branching.
    """

    def is_some(self: Option[T]) -> bool:
        """Return ``True`` if this is ``Some``.

        Subclasses implement this; calling on the base type is not expected.
        """
        raise NotImplementedError

    def is_none(self: Option[T]) -> bool:
        """Return ``True`` if this is ``NOTHING`` (i.e., not ``Some``)."""
        return not self.is_some()

    def map[U](self: Option[T], f: Callable[[T], U]) -> Option[U]:
        """Apply ``f`` to the contained value if ``Some``; otherwise ``NOTHING``.

        Mapping preserves the optional nature: ``Some(x).map(f)`` becomes
        ``Some(f(x))``; ``NOTHING.map(f)`` stays ``NOTHING``.
        """
        return Some(f(self.value)) if isinstance(self, Some) else cast(Option[U], NOTHING)

    def bind[U](self: Option[T], f: Callable[[T], Option[U]]) -> Option[U]:
        """Flat-map with ``f`` returning another ``Option``.

        Also known as ``and_then``/``flat_map``.
        """
        return f(self.value) if isinstance(self, Some) else cast(Option[U], NOTHING)

    async def map_async[U](self: Option[T], f: Callable[[T], Awaitable[U]]) -> Option[U]:
        """Awaitably transform the value if present; otherwise ``NOTHING``.

        Useful for composing async functions over optional values.
        """
        if isinstance(self, Some):
            return Some(await f(self.value))
        return cast(Option[U], NOTHING)

    async def bind_async[U](self: Option[T], f: Callable[[T], Awaitable[Option[U]]]) -> Option[U]:
        """Awaitably flat-map with ``f`` returning an ``Option``."""
        if isinstance(self, Some):
            return await f(self.value)
        return cast(Option[U], NOTHING)

    def get_or[U](self: Option[T], default: U) -> T | U:
        """Unwrap the value or return ``default`` if ``NOTHING``.

        .. deprecated:: 0.3.0
            Use ``unwrap_or`` instead for consistency with Result.
        """
        return self.value if isinstance(self, Some) else default

    def unwrap_or[U](self: Option[T], default: U) -> T | U:
        """Unwrap the value or return ``default`` if ``NOTHING``."""
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

    def to_result[E](self: Option[T], err: E | Callable[[], E]) -> Result[T, E]:
        """Convert Option[T] to Result[T, E] (Some -> Ok; NOTHING -> Err(err))."""
        if isinstance(self, Some):
            return Ok(self.value)
        return Err(err()) if callable(err) else Err(err)

    def match[U](self: Option[T], some: Callable[[T], U], none: Callable[[], U]) -> U:
        """Pattern-match helper."""
        return some(self.value) if isinstance(self, Some) else none()

    def unwrap(self: Option[T]) -> T:
        """Return inner value for Some, else raise ValueError."""
        if isinstance(self, Some):
            return cast(T, self.value)
        raise ValueError("Unwrapped NOTHING")

    def expect(self: Option[T], msg: str) -> T:
        """Return inner value for Some, else raise ValueError with custom message."""
        if isinstance(self, Some):
            return cast(T, self.value)
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Some[T](Option[T]):
    value: T

    def is_some(self: Some[T]) -> bool:
        """``Some`` always reports presence of a value."""
        return True

    def __repr__(self: Some[T]) -> str:  # nicer than dataclass default
        return f"Some({self.value!r})"


@dataclass(frozen=True, slots=True)
class Nothing(Option[None]):
    def is_some(self: Nothing) -> bool:
        """``Nothing`` always reports absence of a value."""
        return False

    def __repr__(self: Nothing) -> str:
        return "NOTHING"


NOTHING = Nothing()


def from_nullable[T](x: T | None) -> Option[T]:
    """Convert a ``T | None`` into ``Option[T]``.

    Returns ``Some(x)`` when ``x`` is not ``None``; otherwise ``NOTHING``.
    """
    return cast(Option[T], NOTHING) if x is None else Some(x)
