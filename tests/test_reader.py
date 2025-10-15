from __future__ import annotations

from fptk.adt.reader import Reader, ask, local

SIX = 6
EIGHT = 8
FORTY_TWO = 42
TEN = 10


def test_reader_map_bind_run() -> None:
    # Test map
    r = ask().map(lambda x: x + 1)
    assert r.run(5) == SIX

    # Test bind
    r2 = ask().bind(lambda x: Reader(lambda _: x * 2))
    assert r2.run(3) == SIX

    # Test chaining
    r3 = ask().bind(lambda x: ask().map(lambda y: x + y))
    assert r3.run(4) == EIGHT


def test_ask_and_local() -> None:
    # ask gets the environment
    assert ask().run(FORTY_TWO) == FORTY_TWO

    # local modifies environment
    r = local(lambda x: x * 2, ask())
    assert r.run(5) == TEN

    # local affects only the subcomputation
    r2 = ask().bind(lambda x: local(lambda y: y + 1, ask().map(lambda z: z * 2)))
    assert r2.run(3) == EIGHT  # (3 + 1) * 2 = 8


def test_reader_repr() -> None:
    r = ask()
    assert "Reader" in repr(r)
