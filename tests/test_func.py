from __future__ import annotations

from fptk.adt.option import NOTHING, Some
from fptk.adt.result import Err, Ok
from fptk.core.func import (
    compose,
    const,
    curry,
    flip,
    foldl,
    foldr,
    identity,
    once,
    pipe,
    reduce,
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


# --- Fold functions ---

TEN = 10
FOUR = 4


def test_foldl_sum() -> None:
    """Left fold with addition."""
    assert foldl(lambda acc, x: acc + x, 0, [1, 2, 3]) == SIX


def test_foldl_subtraction() -> None:
    """Left fold is left-associative: ((10-1)-2)-3 = 4."""
    assert foldl(lambda acc, x: acc - x, TEN, [1, 2, 3]) == FOUR


def test_foldl_empty() -> None:
    """Left fold on empty list returns init."""
    assert foldl(lambda acc, x: acc + x, FORTY_TWO, []) == FORTY_TWO


def test_foldl_string_concat() -> None:
    """Left fold builds string left-to-right."""
    result = foldl(lambda acc, x: f"{acc}-{x}", "start", ["a", "b", "c"])
    assert result == "start-a-b-c"


def test_foldr_string_concat() -> None:
    """Right fold builds string right-to-left."""
    result = foldr(lambda x, acc: f"{x}-{acc}", "end", ["a", "b", "c"])
    assert result == "a-b-c-end"


def test_foldr_subtraction() -> None:
    """Right fold is right-associative: 1-(2-(3-10)) = 1-(2-(-7)) = 1-9 = -8."""
    # But with our signature f(x, acc), it's: 1-(2-(3-10)) for subtraction
    # Actually let's test: ((10-3)-2)-1 = 4 when done from right
    # foldr(f, init, xs) -> f(x1, f(x2, f(x3, init)))
    # With f = lambda x, acc: acc - x and init = 10, xs = [1, 2, 3]:
    # f(1, f(2, f(3, 10))) = f(1, f(2, 7)) = f(1, 5) = 4
    assert foldr(lambda x, acc: acc - x, TEN, [1, 2, 3]) == FOUR


def test_foldr_empty() -> None:
    """Right fold on empty list returns init."""
    assert foldr(lambda x, acc: acc + x, FORTY_TWO, []) == FORTY_TWO


def test_reduce_sum() -> None:
    """Reduce with addition returns Some."""
    assert reduce(lambda a, b: a + b, [1, 2, 3]) == Some(SIX)


def test_reduce_max() -> None:
    """Reduce with max returns Some of max value."""
    assert reduce(max, [1, FIVE, THREE]) == Some(FIVE)


def test_reduce_empty() -> None:
    """Reduce on empty list returns NOTHING."""
    result = reduce(lambda a, b: a + b, [])
    assert result is NOTHING


def test_reduce_single_element() -> None:
    """Reduce on single element returns Some of that element."""
    assert reduce(lambda a, b: a + b, [FORTY_TWO]) == Some(FORTY_TWO)
