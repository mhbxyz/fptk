from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable

from fptk.adt.result import Err, Ok, Result
from fptk.core.func import async_pipe

__all__ = [
    "async_pipe",
    "gather_results",
    "gather_results_accumulate",
]


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
