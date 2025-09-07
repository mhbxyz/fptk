from __future__ import annotations

from fptk.adt.result import Err, Ok
from fptk.core.func import (
    compose,
    const,
    curry,
    flip,
    identity,
    once,
    pipe,
    tap,
    thunk,
    try_catch,
)

# avoid magic number (PLR2004)
EIGHT = 8
SIX = 6
THREE = 3
TWO = 2
FIVE = 5
SEVEN = 7
NINETY_NINE = 99
FORTY_TWO = 42


def inc(x: int) -> int:
    return x + 1


def dbl(x: int) -> int:
    return x * 2


def test_compose() -> None:
    assert compose(dbl, inc)(THREE) == EIGHT


def test_pipe() -> None:
    assert pipe(THREE, inc, dbl) == EIGHT


def test_curry() -> None:
    def add(a: int, b: int, c: int) -> int:
        return a + b + c

    add3 = curry(add)
    assert add3(1)(2)(3) == SIX
    assert add3(1, 2)(3) == SIX
    assert add3(1)(2, 3) == SIX


def test_flip() -> None:
    def sub(a: int, b: int) -> int:  # a - b
        return a - b

    flipped = flip(sub)
    assert sub(FIVE, TWO) == THREE
    assert flipped(FIVE, TWO) == -THREE


def test_tap() -> None:
    out: list[int] = []

    def record(x: int) -> None:
        out.append(x)

    tapped = tap(record)
    assert tapped(FORTY_TWO) == FORTY_TWO
    assert out == [FORTY_TWO]


def test_thunk_memoizes_and_runs_once() -> None:
    calls = {"n": 0}

    def compute() -> int:
        calls["n"] += 1
        return FORTY_TWO

    lazy = thunk(compute)
    # First call evaluates and returns value
    assert lazy() == FORTY_TWO
    # Subsequent calls return cached value without re-running compute
    assert lazy() == FORTY_TWO
    assert lazy() == FORTY_TWO
    assert calls["n"] == 1


def test_identity_and_const() -> None:
    assert identity(FORTY_TWO) == FORTY_TWO
    always_7 = const(SEVEN)
    assert always_7("ignored", key="ignored") == SEVEN


def test_once_runs_only_once() -> None:
    calls = {"n": 0}

    def f(x: int) -> int:
        calls["n"] += 1
        return x * 2

    g = once(f)
    assert g(THREE) == SIX
    assert g(NINETY_NINE) == SIX
    assert calls["n"] == 1


def test_try_catch_ok_and_err() -> None:
    def ok() -> int:
        return 5

    def boom() -> int:
        raise ValueError("x")

    assert try_catch(ok)() == Ok(5)
    r = try_catch(boom)()
    assert isinstance(r, Err)
    assert isinstance(r.error, ValueError)
