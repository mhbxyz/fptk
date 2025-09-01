from __future__ import annotations

from fptk.adt.result import Err, Ok, Result


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
