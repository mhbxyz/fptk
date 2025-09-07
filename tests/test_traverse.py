from __future__ import annotations

from fptk.adt.option import NONE, Some
from fptk.adt.result import Err, Ok
from fptk.adt.traverse import (
    sequence_option,
    sequence_result,
    traverse_option,
    traverse_result,
)

ONE = 1
TWO = 2
THREE = 3
FOUR = 4
SIX = 6
NINE = 9


def test_sequence_option_and_result():
    assert sequence_option([Some(ONE), Some(TWO)]) == Some([ONE, TWO])
    assert sequence_option([Some(ONE), NONE]) is NONE

    assert sequence_result([Ok(ONE), Ok(TWO)]) == Ok([ONE, TWO])
    assert sequence_result([Ok(ONE), Err("e")]) == Err("e")


def test_traverse_option_and_result():
    assert traverse_option([ONE, TWO, THREE], lambda x: Some(x * TWO)) == Some([TWO, FOUR, SIX])
    assert traverse_option([ONE, TWO, THREE], lambda x: NONE if x == TWO else Some(x)) is NONE

    assert traverse_result([ONE, TWO, THREE], lambda x: Ok(x * THREE)) == Ok([THREE, SIX, NINE])
    assert traverse_result([ONE, TWO, THREE], lambda x: Err("bad") if x == TWO else Ok(x)) == Err(
        "bad"
    )
