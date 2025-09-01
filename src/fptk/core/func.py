from __future__ import annotations

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def compose(f: Callable[[U], V], g: Callable[[T], U]) -> Callable[[T], V]:
    """Compose two unary functions: (f ∘ g)(x) = f(g(x))."""

    def h(x: T) -> V:
        return f(g(x))

    return h


def pipe(x: T, *funcs: Callable[[Any], Any]) -> Any:  # noqa: ANN401, UP047
    """Thread a value through a sequence of unary functions.

    Example: pipe(2, lambda x: x + 1, lambda x: x * 3) -> 9
    """
    for f in funcs:
        x = f(x)
    return x


def curry(fn: Callable[P, T]) -> Callable[..., Any]:  # noqa: UP047
    """Curry a function of N positional args into nested unary functions."""

    def curried(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        needed = fn.__code__.co_argcount
        if len(args) + len(kwargs) >= needed:
            return fn(*args, **kwargs)
        return lambda *a, **k: curried(*(args + a), **{**kwargs, **k})

    return curried


def flip(fn: Callable[[T, U], V]) -> Callable[[U, T], V]:  # noqa: UP047
    """Flip the first two arguments of a binary function."""

    def flipped(b: U, a: T) -> V:
        return fn(a, b)

    return flipped
