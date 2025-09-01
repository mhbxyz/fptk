from __future__ import annotations

from collections.abc import Iterable

from fptk.adt.nelist import NonEmptyList

HEAD = "a"
T1 = "b"
T2 = "c"


def test_iter_and_append() -> None:
    nel1 = NonEmptyList(HEAD)
    nel2 = nel1.append(T1)
    nel3 = nel2.append(T2)

    # Original remains unchanged (immutability), appended lists grow
    assert list(nel1) == [HEAD]
    assert list(nel2) == [HEAD, T1]
    assert list(nel3) == [HEAD, T1, T2]


def test_from_iter_constructor() -> None:
    empty: Iterable[str] = []
    assert NonEmptyList.from_iter(empty) is None

    seq: Iterable[str] = [HEAD, T1, T2]
    nel = NonEmptyList.from_iter(seq)
    assert nel is not None
    assert nel.head == HEAD
    assert list(nel) == [HEAD, T1, T2]
