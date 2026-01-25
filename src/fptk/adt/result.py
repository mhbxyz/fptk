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

from collections.abc import Awaitable, Callable
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

    def map[U](self: Result[T, E], f: Callable[[T], U]) -> Ok[U, E] | Result[U, E]:
        """Transform the success value with ``f``; preserve errors.

        ``Ok(x).map(f)`` becomes ``Ok(f(x))``; ``Err(e)`` stays ``Err(e)``.
        """
        if isinstance(self, Ok):
            return Ok(f(self.value))
        return cast(Result[U, E], self)

    def bind[U](self: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Flat-map with ``f`` returning another ``Result``.

        Also known as ``and_then``/``flat_map``.
        """
        if isinstance(self, Ok):
            return f(self.value)
        return cast(Result[U, E], self)

    def and_then[U](self: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Alias for ``bind()``. Named after Rust's Result::and_then."""
        return self.bind(f)

    def flatten(self: Result[T, E]) -> T:
        """Flatten nested ``Result[Result[U, E], E]`` into ``Result[U, E]``.

        Equivalent to ``bind(identity)`` but more readable when you have
        a nested Result from mapping a function that returns Result.

        Example::

            >>> Ok(Ok(5)).flatten()
            Ok(5)
            >>> Ok(Err("inner")).flatten()
            Err('inner')
            >>> Err("outer").flatten()
            Err('outer')
        """
        if isinstance(self, Ok):
            return cast(T, self.value)
        return cast(T, self)

    def zip[U](self: Result[T, E], other: Result[U, E]) -> Result[tuple[T, U], E]:
        """Combine two Results into a Result of tuple.

        Returns ``Ok((a, b))`` if both are ``Ok``; otherwise the first ``Err``.
        """
        if isinstance(self, Ok) and isinstance(other, Ok):
            return Ok((self.value, other.value))
        if isinstance(self, Err):
            return cast(Result[tuple[T, U], E], self)
        return cast(Result[tuple[T, U], E], other)

    def zip_with[U, R](
        self: Result[T, E], other: Result[U, E], f: Callable[[T, U], R]
    ) -> Result[R, E]:
        """Combine two Results with a function.

        Returns ``Ok(f(a, b))`` if both are ``Ok``; otherwise the first ``Err``.
        """
        if isinstance(self, Ok) and isinstance(other, Ok):
            return Ok(f(self.value, other.value))
        if isinstance(self, Err):
            return cast(Result[R, E], self)
        return cast(Result[R, E], other)

    def ap[U, R](self: Result[T, E], other: Result[U, E]) -> Result[R, E]:
        """Apply a wrapped function to a wrapped value (applicative apply).

        If both ``self`` and ``other`` are ``Ok``, applies the function
        inside ``self`` to the value inside ``other``. Otherwise returns
        the first ``Err`` encountered.

        Example::

            >>> Ok(lambda x: x + 1).ap(Ok(5))
            Ok(6)
            >>> Ok(lambda x: x + 1).ap(Err("no value"))
            Err('no value')
            >>> Err("no func").ap(Ok(5))
            Err('no func')

        Useful for curried multi-argument functions::

            >>> def add(a): return lambda b: a + b
            >>> Ok(add).ap(Ok(1)).ap(Ok(2))
            Ok(3)
        """
        if isinstance(self, Ok) and isinstance(other, Ok) and callable(self.value):
            return cast(Result[R, E], Ok(self.value(other.value)))
        if isinstance(self, Err):
            return cast(Result[R, E], self)
        return cast(Result[R, E], other)

    async def map_async[U](self: Result[T, E], f: Callable[[T], Awaitable[U]]) -> Result[U, E]:
        """Awaitably transform the success value; preserve errors."""
        if isinstance(self, Ok):
            return Ok(await f(self.value))
        return cast(Result[U, E], self)

    async def bind_async[U](
        self: Result[T, E], f: Callable[[T], Awaitable[Result[U, E]]]
    ) -> Result[U, E]:
        """Awaitably flat-map with ``f`` returning another ``Result``."""
        if isinstance(self, Ok):
            return await f(self.value)
        return cast(Result[U, E], self)

    def map_err[U](self: Result[T, E], f: Callable[[E], U]) -> Result[T, U]:
        """Transform the error with ``f``; preserve successes."""
        if isinstance(self, Err):
            return Err(f(self.error))
        return cast(Result[T, U], self)

    def recover(self: Result[T, E], f: Callable[[E], T]) -> Result[T, E]:
        """Convert ``Err`` to ``Ok`` by applying ``f`` to the error.

        If this is ``Ok``, returns self unchanged. If this is ``Err(e)``,
        returns ``Ok(f(e))``.

        Example::

            >>> Err("not found").recover(lambda e: "default")
            Ok('default')
            >>> Ok(5).recover(lambda e: 0)
            Ok(5)
        """
        if isinstance(self, Err):
            return Ok(f(self.error))
        return self

    def recover_with(self: Result[T, E], f: Callable[[E], Result[T, E]]) -> Result[T, E]:
        """Convert ``Err`` to another ``Result`` by applying ``f`` to the error.

        If this is ``Ok``, returns self unchanged. If this is ``Err(e)``,
        returns ``f(e)`` which may be ``Ok`` or ``Err``.

        Useful for conditional recovery where some errors can be handled
        and others should propagate.

        Example::

            >>> Err("timeout").recover_with(lambda e: Ok("cached") if e == "timeout" else Err(e))
            Ok('cached')
            >>> Err("fatal").recover_with(lambda e: Ok("cached") if e == "timeout" else Err(e))
            Err('fatal')
            >>> Ok(5).recover_with(lambda e: Ok(0))
            Ok(5)
        """
        if isinstance(self, Err):
            return f(self.error)
        return self

    def unwrap_or[U](self: Result[T, E], default: U) -> T | U:
        """Return inner value for Ok, else provided default."""
        return self.value if isinstance(self, Ok) else default

    def unwrap_or_else[U](self: Result[T, E], f: Callable[[E], U]) -> T | U:
        """Return inner value for Ok, else compute default from error."""
        if isinstance(self, Ok):
            return cast(Ok[T, E], self).value
        return f(cast(Err[T, E], self).error)

    def match[U](self: Result[T, E], ok: Callable[[T], U], err: Callable[[E], U]) -> U:
        """Pattern-match helper."""
        return ok(self.value) if isinstance(self, Ok) else err(cast(Err[T, E], self).error)

    def unwrap(self: Result[T, E]) -> T:
        """Return inner value for Ok, else raise ValueError with error."""
        if isinstance(self, Ok):
            return cast(T, self.value)
        raise ValueError(f"Unwrapped Err: {cast(Err[T, E], self).error!r}")

    def expect(self: Result[T, E], msg: str) -> T:
        """Return inner value for Ok, else raise ValueError with custom message."""
        if isinstance(self, Ok):
            return cast(T, self.value)
        raise ValueError(msg)


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
