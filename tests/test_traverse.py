from __future__ import annotations

import asyncio
from typing import cast

from fptk.adt.option import NOTHING, Option, Some
from fptk.adt.result import Err, Ok, Result
from fptk.adt.traverse import (
    sequence_option,
    sequence_result,
    traverse_option,
    traverse_option_async,
    traverse_option_parallel,
    traverse_result,
    traverse_result_async,
    traverse_result_parallel,
)

ONE = 1
TWO = 2
THREE = 3
FOUR = 4
SIX = 6
NINE = 9


def test_sequence_option_and_result():
    assert sequence_option([Some(ONE), Some(TWO)]) == Some([ONE, TWO])
    assert sequence_option([Some(ONE), NOTHING]) is NOTHING  # pyright: ignore[reportArgumentType]

    assert sequence_result([Ok(ONE), Ok(TWO)]) == Ok([ONE, TWO])
    assert sequence_result([Ok(ONE), Err("e")]) == Err("e")


def test_traverse_option_and_result():
    assert traverse_option([ONE, TWO, THREE], lambda x: Some(x * TWO)) == Some([TWO, FOUR, SIX])
    assert traverse_option([ONE, TWO, THREE], lambda x: NOTHING if x == TWO else Some(x)) is NOTHING  # pyright: ignore[reportArgumentType]

    assert traverse_result([ONE, TWO, THREE], lambda x: Ok(x * THREE)) == Ok([THREE, SIX, NINE])
    assert traverse_result([ONE, TWO, THREE], lambda x: Err("bad") if x == TWO else Ok(x)) == Err(
        "bad"
    )


def test_traverse_option_async_all_some():
    async def async_double(x: int) -> Option[int]:
        return Some(x * TWO)

    async def run():
        return await traverse_option_async([ONE, TWO, THREE], async_double)

    assert asyncio.run(run()) == Some([TWO, FOUR, SIX])


def test_traverse_option_async_with_nothing():
    async def maybe_double(x: int) -> Option[int]:
        return cast(Option[int], NOTHING) if x == TWO else Some(x * TWO)

    async def run():
        return await traverse_option_async([ONE, TWO, THREE], maybe_double)

    assert asyncio.run(run()) is NOTHING


def test_traverse_option_async_empty():
    async def async_double(x: int) -> Option[int]:
        return Some(x * TWO)

    async def run():
        return await traverse_option_async([], async_double)

    assert asyncio.run(run()) == Some([])


def test_traverse_result_async_all_ok():
    async def async_triple(x: int) -> Result[int, str]:
        return Ok(x * THREE)

    async def run():
        return await traverse_result_async([ONE, TWO, THREE], async_triple)

    assert asyncio.run(run()) == Ok([THREE, SIX, NINE])


def test_traverse_result_async_with_err():
    async def maybe_triple(x: int) -> Result[int, str]:
        return Err("bad") if x == TWO else Ok(x * THREE)

    async def run():
        return await traverse_result_async([ONE, TWO, THREE], maybe_triple)

    assert asyncio.run(run()) == Err("bad")


def test_traverse_result_async_empty():
    async def async_triple(x: int) -> Result[int, str]:
        return Ok(x * THREE)

    async def run():
        return await traverse_result_async([], async_triple)

    assert asyncio.run(run()) == Ok([])


# --- Parallel variants ---


def test_traverse_option_parallel_all_some():
    async def async_double(x: int) -> Option[int]:
        return Some(x * TWO)

    async def run():
        return await traverse_option_parallel([ONE, TWO, THREE], async_double)

    assert asyncio.run(run()) == Some([TWO, FOUR, SIX])


def test_traverse_option_parallel_with_nothing():
    async def maybe_double(x: int) -> Option[int]:
        return cast(Option[int], NOTHING) if x == TWO else Some(x * TWO)

    async def run():
        return await traverse_option_parallel([ONE, TWO, THREE], maybe_double)

    assert asyncio.run(run()) is NOTHING


def test_traverse_option_parallel_empty():
    async def async_double(x: int) -> Option[int]:
        return Some(x * TWO)

    async def run():
        return await traverse_option_parallel([], async_double)

    assert asyncio.run(run()) == Some([])


def test_traverse_result_parallel_all_ok():
    async def async_triple(x: int) -> Result[int, str]:
        return Ok(x * THREE)

    async def run():
        return await traverse_result_parallel([ONE, TWO, THREE], async_triple)

    assert asyncio.run(run()) == Ok([THREE, SIX, NINE])


def test_traverse_result_parallel_with_err():
    async def maybe_triple(x: int) -> Result[int, str]:
        return Err("bad") if x == TWO else Ok(x * THREE)

    async def run():
        return await traverse_result_parallel([ONE, TWO, THREE], maybe_triple)

    assert asyncio.run(run()) == Err("bad")


def test_traverse_result_parallel_empty():
    async def async_triple(x: int) -> Result[int, str]:
        return Ok(x * THREE)

    async def run():
        return await traverse_result_parallel([], async_triple)

    assert asyncio.run(run()) == Ok([])
