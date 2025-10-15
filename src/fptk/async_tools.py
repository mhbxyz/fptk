from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar

from fptk.adt.result import Err, Ok, Result

__all__ = [
    "async_pipe",
    "gather_results",
    "gather_results_accumulate",
]

T = TypeVar("T")
E = TypeVar("E")


async def async_pipe(x: object, *funcs: Callable[[object], object]) -> object:
    """Thread a value through possibly-async unary functions (standalone helper).

    Duplicated here to allow import without touching core.func; both versions are equivalent.
    """
    for f in funcs:
        x = f(x)
        if inspect.isawaitable(x):
            x = await x
    return x


async def gather_results[T, E](tasks: Iterable[Awaitable[Result[T, E]]]) -> Result[list[T], E]:
    """Await multiple Result-returning tasks; return first error or all successes.

    Behavior:
    - If all tasks resolve to Ok, returns Ok(list of values) in task order.
    - If any task resolves to Err, returns the first encountered Err (after awaiting all).
      Note: does not cancel remaining tasks; suitable for simple fan-out.
    """
    results = await asyncio.gather(*tasks)
    values: list[T] = []
    first_err: E | None = None
    for r in results:
        if isinstance(r, Ok):
            values.append(r.value)
        elif first_err is None and isinstance(r, Err):
            first_err = r.error
    if first_err is not None:
        return Err(first_err)
    return Ok(values)


async def gather_results_accumulate[T, E](
    tasks: Iterable[Awaitable[Result[T, E]]],
) -> Result[list[T], list[E]]:
    """Await multiple Result tasks; accumulate all errors if any.

    - All Ok -> Ok(list of values)
    - Any Err -> Err(list of errors)
    """
    results = await asyncio.gather(*tasks)
    values: list[T] = []
    errors: list[E] = []
    for r in results:
        if isinstance(r, Ok):
            values.append(r.value)
        elif isinstance(r, Err):
            errors.append(r.error)
    if errors:
        return Err(errors)
    return Ok(values)
