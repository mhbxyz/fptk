from __future__ import annotations

from fptk.core.func import compose, curry, flip, pipe, tap

# avoid magic number (PLR2004)
EIGHT = 8
SIX = 6
THREE = 3
FORTY_TWO = 42


def inc(x: int) -> int:
    return x + 1


def dbl(x: int) -> int:
    return x * 2


def test_compose() -> None:
    assert compose(dbl, inc)(3) == EIGHT


def test_pipe() -> None:
    assert pipe(3, inc, dbl) == EIGHT


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
    assert sub(5, 2) == THREE
    assert flipped(5, 2) == -THREE


def test_tap() -> None:
    out: list[int] = []

    def record(x: int) -> None:
        out.append(x)

    tapped = tap(record)
    assert tapped(42) == FORTY_TWO
    assert out == [42]
