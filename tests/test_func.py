from __future__ import annotations

from fptk.core.func import compose, curry, pipe

EXPECTED = 8  # avoid magic number (PLR2004)
SIX = 6  # avoid magic number (PLR2004)


def inc(x: int) -> int:
    return x + 1


def dbl(x: int) -> int:
    return x * 2


def test_compose() -> None:
    assert compose(dbl, inc)(3) == EXPECTED


def test_pipe() -> None:
    assert pipe(3, inc, dbl) == EXPECTED


def test_curry() -> None:
    def add(a: int, b: int, c: int) -> int:
        return a + b + c

    add3 = curry(add)
    assert add3(1)(2)(3) == SIX
    assert add3(1, 2)(3) == SIX
    assert add3(1)(2, 3) == SIX
