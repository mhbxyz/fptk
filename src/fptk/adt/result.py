"""Result (Ok/Err) — success or failure with typed error.

The ``Result[T, E]`` algebraic data type represents computations that may
succeed with a value of type ``T`` or fail with an error of type ``E``:

- ``Ok(value)``: success variant wrapping a value ``T``
- ``Err(error)``: failure variant wrapping an error ``E``

Combinators include ``map`` (transform success), ``bind`` (flat-map), and
``map_err`` (transform error), allowing ergonomic composition without ``try``/``except``.

Examples:

    >>> from fptk.adt.result import Ok, Err
    >>> Ok(2).map(lambda x: x + 1)
    Ok(value=3)
    >>> Err("boom").map(lambda x: x + 1)
    Err(error='boom')
    >>> Ok("7").bind(lambda s: Ok(int(s)))
    Ok(value=7)
    >>> Err("boom").map_err(lambda s: s.upper())
    Err(error='BOOM')
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, cast

__all__ = [
    "Result",
    "Ok",
    "Err",
]

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


class Result[T, E]:
    """Computation that may succeed (``Ok``) or fail (``Err``)."""

    def is_ok(self) -> bool:
        """Return ``True`` if this is ``Ok``."""
        raise NotImplementedError

    def is_err(self) -> bool:
        """Return ``True`` if this is ``Err`` (not ``Ok``)."""
        return not self.is_ok()

    def map(self, f: Callable[[T], U]) -> Result[U, E]:
        """Transform the success value with ``f``; preserve errors.

        ``Ok(x).map(f)`` becomes ``Ok(f(x))``; ``Err(e)`` stays ``Err(e)``.
        """
        return Ok(f(self.value)) if isinstance(self, Ok) else cast(Result[U, E], self)

    def bind(self, f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Flat-map with ``f`` returning another ``Result``.

        Also known as ``and_then``/``flat_map``.
        """
        return f(self.value) if isinstance(self, Ok) else cast(Result[U, E], self)

    def map_err(self, f: Callable[[E], U]) -> Result[T, U]:
        """Transform the error with ``f``; preserve successes."""
        return Err(f(self.error)) if isinstance(self, Err) else cast(Result[T, U], self)


@dataclass(frozen=True, slots=True)
class Ok[T, E](Result[T, E]):
    """Success variant wrapping a value ``T``."""

    value: T

    def is_ok(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class Err[T, E](Result[T, E]):
    """Failure variant wrapping an error ``E``."""

    error: E

    def is_ok(self) -> bool:
        return False
