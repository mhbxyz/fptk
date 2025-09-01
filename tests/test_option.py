from __future__ import annotations

from typing import cast

from fptk.adt.option import NONE, Option, Some, from_nullable

TEN = 10
ZERO = 0


def test_option_map_bind() -> None:
    assert from_nullable("x").map(lambda s: s.upper()).is_some()
    assert from_nullable(None).map(lambda s: s).is_none()

    def to_int(s: str) -> Option[int]:
        try:
            return Some(int(s))
        except ValueError:
            return cast(Option[int], NONE)

    assert Some("7").bind(to_int).is_some()
    assert Some("x").bind(to_int).is_none()


def test_get_or_iter() -> None:
    assert Some(TEN).get_or(ZERO) == TEN
    assert NONE.get_or(ZERO) == ZERO
    assert list(Some("a").iter()) == ["a"]
    assert list(NONE.iter()) == []
