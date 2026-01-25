from __future__ import annotations

from typing import cast

from fptk.adt.option import NOTHING, Option, Some, from_nullable
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
            return cast(Option[int], NOTHING)

    assert Some("7").bind(to_int).is_some()
    assert Some("x").bind(to_int).is_none()


def test_get_or_iter() -> None:
    assert Some(TEN).get_or(ZERO) == TEN
    assert NOTHING.get_or(ZERO) == ZERO
    assert list(Some("a").iter()) == ["a"]
    assert list(NOTHING.iter()) == []


def test_option_to_result_and_or_else_and_match() -> None:
    assert Some(2).to_result("e") == Ok(2)
    assert NOTHING.to_result(lambda: "e") == Err("e")

    assert Some(1).or_else(Some(9)) == Some(1)
    assert NOTHING.or_else(lambda: Some(9)) == Some(9)

    assert Some("x").match(lambda s: s.upper(), lambda: "-") == "X"
    assert NOTHING.match(lambda s: s, lambda: "-") == "-"


def test_option_repr() -> None:
    assert repr(Some(3)) == "Some(3)"
    assert repr(NOTHING) == "NOTHING"


def test_option_zip() -> None:
    # Both Some -> Some of tuple
    assert Some(1).zip(Some("a")) == Some((1, "a"))

    # First NOTHING -> NOTHING
    assert NOTHING.zip(Some(1)) == NOTHING

    # Second NOTHING -> NOTHING
    assert Some(1).zip(NOTHING) == NOTHING

    # Both NOTHING -> NOTHING
    assert NOTHING.zip(NOTHING) == NOTHING


def test_option_zip_with() -> None:
    # Both Some -> apply function
    assert Some(2).zip_with(Some(3), lambda a, b: a + b) == Some(5)
    assert Some("hello").zip_with(Some(" world"), lambda a, b: a + b) == Some("hello world")

    # Any NOTHING -> NOTHING
    assert NOTHING.zip_with(Some(1), lambda a, b: a + b) == NOTHING
    assert Some(1).zip_with(NOTHING, lambda a, b: a + b) == NOTHING


def test_option_and_then_alias() -> None:
    # and_then is alias for bind
    assert Some(5).and_then(lambda x: Some(x + 1)) == Some(6)
    assert NOTHING.and_then(lambda x: Some(x + 1)) == NOTHING


def test_option_filter() -> None:
    # Some with passing predicate -> same Some
    assert Some(5).filter(lambda x: x > 3) == Some(5)

    # Some with failing predicate -> NOTHING
    assert Some(2).filter(lambda x: x > 3) == NOTHING

    # NOTHING -> NOTHING regardless of predicate
    assert NOTHING.filter(lambda x: x > 3) == NOTHING

    # Edge case: predicate returns False for falsy value
    assert Some(0).filter(lambda x: x > 0) == NOTHING
    assert Some(0).filter(lambda x: x == 0) == Some(0)


def test_option_flatten() -> None:
    # Some(Some(x)) -> Some(x)
    assert Some(Some(5)).flatten() == Some(5)

    # Some(NOTHING) -> NOTHING
    assert Some(NOTHING).flatten() == NOTHING

    # NOTHING -> NOTHING
    assert NOTHING.flatten() == NOTHING
