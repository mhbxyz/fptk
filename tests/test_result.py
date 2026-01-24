from __future__ import annotations

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
