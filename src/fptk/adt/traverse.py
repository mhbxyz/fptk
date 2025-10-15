"""Sequence/traverse utilities for ``Option`` and ``Result``.

Use these when you want to turn many small computations into one outcome,
preserving the first absence/error and avoiding manual loops and conditionals.

What they do (all fail‑fast)
- ``sequence_option(xs)``: collect ``Some`` values into ``Some[list]``; return
  ``NOTHING`` on the first ``NOTHING``.
- ``traverse_option(xs, f)``: map with ``f: A -> Option[B]`` and collect; short‑
  circuits to ``NOTHING`` on the first missing value.
- ``sequence_result(xs)``: collect ``Ok`` values into ``Ok[list]``; return the
  first ``Err`` encountered.
- ``traverse_result(xs, f)``: map with ``f: A -> Result[B, E]`` and collect;
  short‑circuits on the first ``Err``.

Practical notes
- Order is preserved; processing stops immediately on the first failure/absence.
- Prefer ``traverse_*`` when mapping with a function that already returns an ADT.
- These helpers compose nicely with ``Option``/``Result`` methods and keep
  “happy path” linear and readable.

Quick examples

    >>> from fptk.adt.option import Some, NOTHING
    >>> sequence_option([Some(1), Some(2)])
    Some([1, 2])
    >>> sequence_option([Some(1), NOTHING])
    NOTHING
    >>> traverse_option([1, 2, 3], lambda x: Some(x * 2))
    Some([2, 4, 6])
    >>> traverse_option([1, 2, 3], lambda x: NOTHING if x == 2 else Some(x))
    NOTHING

    >>> from fptk.adt.result import Ok, Err
    >>> sequence_result([Ok(1), Ok(2)])
    Ok([1, 2])
    >>> sequence_result([Ok(1), Err('e')])
    Err('e')
    >>> traverse_result([1, 2, 3], lambda x: Ok(x * 2))
    Ok([2, 4, 6])
    >>> traverse_result([1, 2, 3], lambda x: Err('boom') if x == 2 else Ok(x))
    Err('boom')
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import cast

from fptk.adt.option import NOTHING, Nothing, Option, Some
from fptk.adt.result import Err, Ok, Result

__all__ = [
    "sequence_option",
    "traverse_option",
    "sequence_result",
    "traverse_result",
    "traverse_option_async",
    "traverse_result_async",
]


def sequence_option[A](xs: Iterable[Option[A]]) -> Option[list[A]] | Nothing:
    """Convert Iterable[Option[A]] -> Option[list[A]] (NOTHING if any item is NOTHING)."""
    out: list[A] = []
    for x in xs:
        if isinstance(x, Some):
            out.append(x.value)
        else:
            return NOTHING
    return Some(out)


def traverse_option[A, B](
    xs: Iterable[A], f: Callable[[A], Option[B]]
) -> Option[list[B]] | Nothing:
    """Map with f and sequence (fail on first NOTHING)."""
    out: list[B] = []
    for x in xs:
        ox = f(x)
        if isinstance(ox, Some):
            out.append(ox.value)
        else:
            return NOTHING
    return Some(out)


def sequence_result[A, E](xs: Iterable[Result[A, E]]) -> Result[list[A], E]:
    """Convert Iterable[Result[A, E]] -> Result[list[A], E] (fail-fast on first Err)."""
    out: list[A] = []
    for x in xs:
        if isinstance(x, Ok):
            out.append(x.value)
        elif isinstance(x, Err):
            return Err(x.error)
        else:  # pragma: no cover - unreachable with current Result variants
            raise TypeError("Unexpected Result variant")
    return Ok(out)


def traverse_result[A, B, E](xs: Iterable[A], f: Callable[[A], Result[B, E]]) -> Result[list[B], E]:
    """Map with f and sequence (fail-fast)."""
    out: list[B] = []
    for x in xs:
        rx = f(x)
        if isinstance(rx, Ok):
            out.append(rx.value)
        elif isinstance(rx, Err):
            return Err(rx.error)
        else:  # pragma: no cover - unreachable with current Result variants
            raise TypeError("Unexpected Result variant")
    return Ok(out)


async def traverse_option_async[A, B](
    xs: Iterable[A], f: Callable[[A], Awaitable[Option[B]]]
) -> Option[list[B]]:
    """Async map with f and sequence (fail on first NOTHING)."""
    out: list[B] = []
    for x in xs:
        ox = await f(x)
        if isinstance(ox, Some):
            out.append(ox.value)
        else:
            return cast(Option[list[B]], NOTHING)
    return Some(out)


async def traverse_result_async[A, B, E](
    xs: Iterable[A], f: Callable[[A], Awaitable[Result[B, E]]]
) -> Result[list[B], E]:
    """Async map with f and sequence (fail-fast)."""
    out: list[B] = []
    for x in xs:
        rx = await f(x)
        if isinstance(rx, Ok):
            out.append(rx.value)
        elif isinstance(rx, Err):
            return Err(rx.error)
        else:  # pragma: no cover - unreachable with current Result variants
            raise TypeError("Unexpected Result variant")
    return Ok(out)
