from __future__ import annotations

from typing import cast

from fptk.adt.option import NONE, Option, Some, from_nullable
from fptk.adt.result import Err, Ok

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


def test_option_to_result_and_or_else_and_match() -> None:
    assert Some(2).to_result("e") == Ok(2)
    assert NONE.to_result(lambda: "e") == Err("e")

    assert Some(1).or_else(Some(9)) == Some(1)
    assert NONE.or_else(lambda: Some(9)) == Some(9)

    assert Some("x").match(lambda s: s.upper(), lambda: "-") == "X"
    assert NONE.match(lambda s: s, lambda: "-") == "-"


def test_option_repr() -> None:
    assert repr(Some(3)) == "Some(3)"
    assert repr(NONE) == "NONE"
