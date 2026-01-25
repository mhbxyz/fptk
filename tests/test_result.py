from __future__ import annotations

import pytest

from fptk.adt.result import Err, Ok, Result

THREE = 3
FOUR = 4
ZERO = 0


def test_result_chain() -> None:
    def parse(s: str) -> Result[int, str]:
        try:
            return Ok(int(s))
        except ValueError:
            return Err("not int")

    def non_neg(x: int) -> Result[int, str]:
        return Ok(x) if x >= 0 else Err("neg")

    assert parse("5").bind(non_neg).map(lambda x: x * 2).is_ok()
    assert parse("-1").bind(non_neg).is_err()
    assert parse("x").is_err()


def test_map_err_unwraps() -> None:
    e: Result[int, str] = Err("boom").map_err(lambda s: s.upper())
    assert e.is_err()
    assert isinstance(e, Err)


def test_result_unwrap_and_match_and_repr() -> None:
    assert Ok(THREE).unwrap_or(ZERO) == THREE
    assert Err("e").unwrap_or(ZERO) == ZERO

    assert Ok(THREE).unwrap_or_else(lambda e: ZERO) == THREE
    assert Err("boom").unwrap_or_else(lambda e: len(e)) == FOUR

    assert Ok("a").match(lambda s: s + "!", lambda e: "-") == "a!"
    assert Err("x").match(lambda s: s, lambda e: e.upper()) == "X"

    assert repr(Ok(1)) == "Ok(1)"
    assert repr(Err("e")) == "Err('e')"


def test_result_zip() -> None:
    # Both Ok -> Ok of tuple
    assert Ok(1).zip(Ok("a")) == Ok((1, "a"))

    # First Err -> first Err
    assert Err("e1").zip(Ok(1)) == Err("e1")

    # Second Err -> second Err
    assert Ok(1).zip(Err("e2")) == Err("e2")

    # Both Err -> first Err
    assert Err("e1").zip(Err("e2")) == Err("e1")


def test_result_zip_with() -> None:
    # Both Ok -> apply function
    assert Ok(2).zip_with(Ok(3), lambda a, b: a + b) == Ok(5)
    assert Ok("hello").zip_with(Ok(" world"), lambda a, b: a + b) == Ok("hello world")

    # Any Err -> Err (first one)
    assert Err("e").zip_with(Ok(1), lambda a, b: a + b) == Err("e")
    assert Ok(1).zip_with(Err("e"), lambda a, b: a + b) == Err("e")


def test_result_and_then_alias() -> None:
    # and_then is alias for bind
    assert Ok(5).and_then(lambda x: Ok(x + 1)) == Ok(6)
    assert Err("e").and_then(lambda x: Ok(x + 1)) == Err("e")


def test_result_flatten() -> None:
    # Ok(Ok(x)) -> Ok(x)
    assert Ok(Ok(5)).flatten() == Ok(5)

    # Ok(Err(e)) -> Err(e)
    assert Ok(Err("inner")).flatten() == Err("inner")

    # Err(e) -> Err(e)
    assert Err("outer").flatten() == Err("outer")


def test_result_recover() -> None:
    # Err -> Ok with recovery function
    assert Err("not found").recover(lambda e: "default") == Ok("default")
    assert Err("error").recover(lambda e: len(e)) == Ok(5)

    # Ok passes through unchanged
    assert Ok(5).recover(lambda e: 0) == Ok(5)
    assert Ok("value").recover(lambda e: "fallback") == Ok("value")


def test_result_recover_with() -> None:
    # Err -> Ok (successful recovery)
    assert Err("timeout").recover_with(lambda e: Ok("cached")) == Ok("cached")

    # Err -> Err (recovery fails or chooses not to recover)
    assert Err("fatal").recover_with(lambda e: Err(f"unrecoverable: {e}")) == Err(
        "unrecoverable: fatal"
    )

    # Conditional recovery
    def try_recover(e: str) -> Result[str, str]:
        if e == "timeout":
            return Ok("cached")
        return Err(e)

    assert Err("timeout").recover_with(try_recover) == Ok("cached")
    assert Err("fatal").recover_with(try_recover) == Err("fatal")

    # Ok passes through unchanged
    assert Ok(5).recover_with(lambda e: Ok(0)) == Ok(5)
    assert Ok("value").recover_with(lambda e: Err("ignored")) == Ok("value")


def test_result_ap() -> None:
    # Success case: apply wrapped function to wrapped value
    assert Ok(lambda x: x + 1).ap(Ok(5)) == Ok(6)
    assert Ok(lambda s: s.upper()).ap(Ok("hello")) == Ok("HELLO")

    # Failure propagation: first Err wins
    assert Ok(lambda x: x + 1).ap(Err("no value")) == Err("no value")
    assert Err("no func").ap(Ok(5)) == Err("no func")
    assert Err("first").ap(Err("second")) == Err("first")

    # Curried multi-argument functions
    def add(a: int):  # noqa: ANN202
        return lambda b: a + b

    assert Ok(add).ap(Ok(1)).ap(Ok(2)) == Ok(3)

    # Error at any step propagates
    assert Ok(add).ap(Err("e1")).ap(Ok(2)) == Err("e1")
    assert Ok(add).ap(Ok(1)).ap(Err("e2")) == Err("e2")


def test_unwrap_err_raises() -> None:
    """unwrap() on Err raises ValueError with error value."""
    with pytest.raises(ValueError, match="Unwrapped Err"):
        Err("error").unwrap()


def test_expect_err_raises() -> None:
    """expect() on Err raises ValueError with custom message."""
    with pytest.raises(ValueError, match="custom message"):
        Err("error").expect("custom message")
