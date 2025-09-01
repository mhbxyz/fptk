"""Validation helpers that accumulate errors applicatively.

This module provides ``validate_all``, a combinator that runs multiple
validation checks on a value and collects all error messages using the
``NonEmptyList`` ADT instead of failing fast. It composes over ``Result`` so it
fits naturally with other success/failure pipelines.

Example:
    >>> from fptk.validate import validate_all
    >>> from fptk.adt.result import Ok, Err
    >>> def min_len(n: int):
    ...     def check(s: str):
    ...         return Ok(s) if len(s) >= n else Err(f"len<{n}")
    ...     return check
    >>> def has_digit(s: str):
    ...     return Ok(s) if any(c.isdigit() for c in s) else Err("no digit")
    >>> validate_all([min_len(3), has_digit], "ab3").is_ok()
    True
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

from fptk.adt.nelist import NonEmptyList
from fptk.adt.result import Err, Ok, Result

__all__ = [
    "validate_all",
]

T = TypeVar("T")
E = TypeVar("E")


def validate_all[T, E](
    checks: Iterable[Callable[[T], Result[T, E]]], value: T
) -> Result[T, NonEmptyList[E]]:
    """Run checks on ``value`` and accumulate all errors.

    - On success for all checks, returns ``Ok`` with the (possibly transformed)
      value.
    - On any failure, returns ``Err`` with a ``NonEmptyList`` of all collected
      errors in order.
    """
    errors: NonEmptyList[E] | None = None
    cur = value
    for check in checks:
        r = check(cur)
        if isinstance(r, Ok):
            cur = r.value
        elif isinstance(r, Err):
            err = r.error
            errors = NonEmptyList(err) if errors is None else errors.append(err)
    return Ok(cur) if errors is None else Err(errors)
