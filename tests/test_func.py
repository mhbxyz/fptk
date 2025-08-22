from __future__ import annotations

from funktools.core.func import compose, pipe

EXPECTED = 8  # avoid magic number (PLR2004)


def inc(x: int) -> int:
    return x + 1


def dbl(x: int) -> int:
    return x * 2


def test_compose() -> None:
    assert compose(dbl, inc)(3) == EXPECTED


def test_pipe() -> None:
    assert pipe(3, inc, dbl) == EXPECTED
