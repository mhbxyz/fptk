"""Result (Ok/Err) — success or failure with typed error.

Use ``Result`` when you want to model recoverable failures without exceptions.
It keeps error types explicit and composes cleanly across multiple steps, which
is great for parsing, validation, I/O, and “railway‑oriented” flows.

The ``Result[T, E]`` algebraic data type represents computations that may
succeed with a value of type ``T`` or fail with an error of type ``E``:

- ``Ok(value)``: success variant wrapping a value ``T``
- ``Err(error)``: failure variant wrapping an error ``E``

Everyday usage
- ``map(f)`` transforms the success value; errors pass through unchanged.
- ``bind(f)`` (aka ``and_then``) chains computations that return ``Result``;
  the first ``Err`` short‑circuits the chain.
- ``map_err(f)`` transforms the error while preserving successes.
- ``unwrap_or(default)``/``unwrap_or_else(f)`` provide safe fallbacks.
- ``match(ok, err)`` is a straightforward way to consume success vs error.

Interop and practicality
- Pairs well with ``traverse_result`` helpers to work over collections.
- Converting exceptions: wrap functions with ``try_catch`` from ``fptk.core.func``.
- Prefer small error types (``str``, ``Enum``, lightweight dataclass) for clarity.
- Instances are immutable and hashable; equality compares contained value/error.
- There’s minor call overhead; avoid excessively deep chains in hot paths.

Quick examples

    >>> from fptk.adt.result import Ok, Err
    >>> Ok(2).map(lambda x: x + 1)
    Ok(3)
    >>> Err("boom").map(lambda x: x + 1)
    Err('boom')
    >>> Ok("7").bind(lambda s: Ok(int(s)))
    Ok(7)
    >>> Err("boom").map_err(lambda s: s.upper())
    Err('BOOM')
    >>> Err("e").unwrap_or(0)
    0
    >>> Ok(5).unwrap_or_else(lambda e: 0)
    5
    >>> Ok(2).match(lambda x: x * 2, lambda e: 0)
    4
    >>> from fptk.core.func import try_catch
    >>> try_catch(lambda: int("7"))()
    Ok(7)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

__all__ = [
    "Result",
    "Ok",
    "Err",
]


class Result[T, E]:
    """Computation that may succeed (``Ok``) or fail (``Err``)."""

    def is_ok(self: Result[T, E]) -> bool:
        """Return ``True`` if this is ``Ok``."""
        raise NotImplementedError

    def is_err(self: Result[T, E]) -> bool:
        """Return ``True`` if this is ``Err`` (not ``Ok``)."""
        return not self.is_ok()

    def map[U](self: Result[T, E], f: Callable[[T], U]) -> Result[U, E]:
        """Transform the success value with ``f``; preserve errors.

        ``Ok(x).map(f)`` becomes ``Ok(f(x))``; ``Err(e)`` stays ``Err(e)``.
        """
        return Ok(f(self.value)) if isinstance(self, Ok) else cast(Result[U, E], self)

    def bind[U](self: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Flat-map with ``f`` returning another ``Result``.

        Also known as ``and_then``/``flat_map``.
        """
        return f(self.value) if isinstance(self, Ok) else cast(Result[U, E], self)

    def map_err[U](self: Result[T, E], f: Callable[[E], U]) -> Result[T, U]:
        """Transform the error with ``f``; preserve successes."""
        return Err(f(self.error)) if isinstance(self, Err) else cast(Result[T, U], self)

    def unwrap_or[U](self: Result[T, E], default: U) -> T | U:
        """Return inner value for Ok, else provided default."""
        return self.value if isinstance(self, Ok) else default

    def unwrap_or_else[U](self: Result[T, E], f: Callable[[E], U]) -> T | U:
        """Return inner value for Ok, else compute default from error."""
        return self.value if isinstance(self, Ok) else f(cast(Err[T, E], self).error)

    def match[U](self: Result[T, E], ok: Callable[[T], U], err: Callable[[E], U]) -> U:
        """Pattern-match helper."""
        return ok(self.value) if isinstance(self, Ok) else err(cast(Err[T, E], self).error)


@dataclass(frozen=True, slots=True)
class Ok[T, E](Result[T, E]):
    """Success variant wrapping a value ``T``."""

    value: T

    def is_ok(self: Ok[T, E]) -> bool:
        return True

    def __repr__(self: Ok[T, E]) -> str:
        return f"Ok({self.value!r})"


@dataclass(frozen=True, slots=True)
class Err[T, E](Result[T, E]):
    """Failure variant wrapping an error ``E``."""

    error: E

    def is_ok(self: Err[T, E]) -> bool:
        return False

    def __repr__(self: Err[T, E]) -> str:
        return f"Err({self.error!r})"
