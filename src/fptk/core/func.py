"""Core function combinators for small, pragmatic functional programming.

These helpers are lightweight glue for everyday Python: make pipelines readable,
shape functions to better fit higher-order APIs, and keep side effects explicit.
They are tiny wrappers around plain callables — no metaprogramming or magic.

What you’ll reach for most
- ``pipe(x, *fs)``: prefer ``pipe(x, f, g, h)`` over nested calls ``h(g(f(x)))``.
- ``compose(f, g)``: build small building blocks, then compose into handlers.
- ``curry(fn)``: create unary-first variants so functions slot into maps/filters.
- ``flip(fn)``: fix awkward argument order to enable partials or mapping.
- ``tap(f)``: log/inspect/notify without breaking the data flow.

Memoization and once-only
- ``thunk(f)`` memoizes a zero-arg computation (simple, lazy value).
- ``once(fn)`` runs a function at most once and returns the first result for all
  future calls (ignores later arguments) — useful for setup hooks.

Errors as values
- ``try_catch(fn)`` converts exceptions into ``Result`` values (``Ok``/``Err``),
  which pairs well with ``Result`` combinators and traverse helpers.

Small utilities
- ``identity(x)`` returns the input unchanged (handy default function).
- ``const(x)`` ignores all arguments and returns ``x`` (useful in callbacks).

Practical notes
- These are convenience layers; Python call overhead is not zero. Keep chains
  reasonable in hot paths.
- ``curry`` counts positional parameters via ``__code__.co_argcount``. It works
  for regular positional arguments; keyword-only and varargs are supported at
  call time but aren’t part of the “enough arguments” check.

Quick examples
    >>> from fptk.core.func import (
    ...     compose, pipe, curry, flip, tap, thunk,
    ...     identity, const, once, try_catch,
    ... )
    >>> pipe(2, lambda x: x + 1, lambda x: x * 3)
    9
    >>> compose(lambda x: x * 2, lambda x: x + 1)(3)
    8
    >>> add = lambda a, b: a + b
    >>> curry(add)(2)(3)
    5
    >>> tap(print)("hi")  # prints and returns the value
    'hi'
    >>> thunk(lambda: 42)()
    42
    >>> once(lambda x: x * 2)(3)
    6
    >>> const(7)("ignored", key="ignored")
    7
    >>> try_catch(lambda: 5)()
    Ok(5)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fptk.adt.result import Err, Ok, Result

__all__ = [
    "compose",
    "pipe",
    "curry",
    "flip",
    "tap",
    "thunk",
    "identity",
    "const",
    "once",
    "try_catch",
]


def compose[T, U, V](f: Callable[[U], V], g: Callable[[T], U]) -> Callable[[T], V]:
    """Compose two unary functions: (f ∘ g)(x) = f(g(x))."""

    def h(x: T) -> V:
        return f(g(x))

    return h


def pipe[T](x: T, *funcs: Callable[[Any], Any]) -> Any:  # noqa: ANN401
    """Thread a value through a sequence of unary functions.

    Example: pipe(2, lambda x: x + 1, lambda x: x * 3) -> 9
    """
    for f in funcs:
        x = f(x)
    return x


def curry[T, **P](fn: Callable[P, T]) -> Callable[..., Any]:
    """Curry a function of N positional args into nested unary functions."""

    def curried(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        needed = fn.__code__.co_argcount
        if len(args) + len(kwargs) >= needed:
            return fn(*args, **kwargs)
        return lambda *a, **k: curried(*(args + a), **{**kwargs, **k})

    return curried


def flip[T, U, V](fn: Callable[[T, U], V]) -> Callable[[U, T], V]:
    """Flip the first two arguments of a binary function."""

    def flipped(b: U, a: T) -> V:
        return fn(a, b)

    return flipped


def tap[T](f: Callable[[T], Any]) -> Callable[[T], T]:
    """Run a side effect on a value and return the original value."""

    def inner(x: T) -> T:
        f(x)
        return x

    return inner


def thunk[T](f: Callable[[], T]) -> Callable[[], T | None]:
    """Memoized nullary function (simple lazy thunk)."""
    evaluated = False
    value: T | None = None

    def wrapper() -> T | None:
        nonlocal evaluated, value
        if not evaluated:
            value = f()
            evaluated = True
        return value

    return wrapper


def identity[T](x: T) -> T:
    """Return the input unchanged."""
    return x


def const[T](x: T) -> Callable[..., T]:
    """Return a function that ignores its arguments and returns x."""

    def inner(*_: object, **__: object) -> T:
        return x

    return inner


def once[T, **P](fn: Callable[P, T]) -> Callable[P, T | None]:
    """Wrap fn so it runs at most once; memoize the first result."""
    called = False
    result: T | None = None

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        nonlocal called, result
        if not called:
            result = fn(*args, **kwargs)
            called = True
        return result

    return wrapper


def try_catch[T, **P](fn: Callable[P, T]) -> Callable[P, Result[T, Exception]]:
    """Wrap fn to return Ok(...) or Err(Exception) instead of raising.

    We catch Exception (not BaseException) to avoid swallowing KeyboardInterrupt/SystemExit.
    """

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T, Exception]:
        try:
            return Ok(fn(*args, **kwargs))
        except Exception as e:  # noqa: BLE001
            return Err(e)

    return wrapper
