"""Sequence/traverse utilities for ``Option`` and ``Result``.

Use these when you want to turn many small computations into one outcome,
preserving the first absence/error and avoiding manual loops and conditionals.

What they do (all fail‑fast)
- ``sequence_option(xs)``: collect ``Some`` values into ``Some[list]``; return
  ``NONE`` on the first ``NONE``.
- ``traverse_option(xs, f)``: map with ``f: A -> Option[B]`` and collect; short‑
  circuits to ``NONE`` on the first missing value.
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

    >>> from fptk.adt.option import Some, NONE
    >>> sequence_option([Some(1), Some(2)])
    Some([1, 2])
    >>> sequence_option([Some(1), NONE])
    NONE
    >>> traverse_option([1, 2, 3], lambda x: Some(x * 2))
    Some([2, 4, 6])
    >>> traverse_option([1, 2, 3], lambda x: NONE if x == 2 else Some(x))
    NONE

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

from collections.abc import Callable, Iterable

from fptk.adt.option import NONE, Option, Some, _None
from fptk.adt.result import Err, Ok, Result

__all__ = [
    "sequence_option",
    "traverse_option",
    "sequence_result",
    "traverse_result",
]


def sequence_option[A](xs: Iterable[Option[A]]) -> Option[list[A]] | _None:
    """Convert Iterable[Option[A]] -> Option[list[A]] (NONE if any item is NONE)."""
    out: list[A] = []
    for x in xs:
        if isinstance(x, Some):
            out.append(x.value)
        else:
            return NONE
    return Some(out)


def traverse_option[A, B](xs: Iterable[A], f: Callable[[A], Option[B]]) -> Option[list[B]] | _None:
    """Map with f and sequence (fail on first NONE)."""
    out: list[B] = []
    for x in xs:
        ox = f(x)
        if isinstance(ox, Some):
            out.append(ox.value)
        else:
            return NONE
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
