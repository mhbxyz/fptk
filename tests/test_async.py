import asyncio

from fptk import async_tools
from fptk.adt import option, result
from fptk.core import func


async def _ainc(x: int) -> int:
    await asyncio.sleep(0)
    return x + 1


async def _aok(x: int) -> result.Ok[int, str]:
    await asyncio.sleep(0)
    return result.Ok(x)


async def _aerr(msg: str) -> result.Err[int, str]:
    await asyncio.sleep(0)
    return result.Err(msg)


NINE = 9
THREE = 3


def test_async_pipe_mixed_sync_async():
    async def run():
        def times3(x: int) -> int:
            return x * 3

        return await func.async_pipe(2, _ainc, times3)

    assert asyncio.run(run()) == NINE


def test_async_pipe_util_equivalence():
    async def run():
        return await async_tools.async_pipe(1, _ainc, _ainc)

    assert asyncio.run(run()) == THREE


def test_option_map_bind_async():
    async def some_plus_one(x: int):
        await asyncio.sleep(0)
        return option.Some(x + 1)

    async def run():
        assert await option.Some(2).map_async(_ainc) == option.Some(3)
        assert await option.NOTHING.map_async(_ainc) is option.NOTHING
        assert await option.Some(2).bind_async(some_plus_one) == option.Some(3)
        assert await option.NOTHING.bind_async(some_plus_one) is option.NOTHING

    asyncio.run(run())


def test_result_map_bind_async():
    async def run():
        assert await result.Ok[int, str](2).map_async(_ainc) == result.Ok(3)
        assert await result.Err[int, str]("e").map_async(_ainc) == result.Err("e")
        assert await result.Ok[int, str](2).bind_async(lambda x: _aok(x + 1)) == result.Ok(3)
        assert await result.Err[int, str]("e").bind_async(lambda x: _aok(x + 1)) == result.Err("e")

    asyncio.run(run())


def test_gather_results_success_and_error():
    async def run_ok():
        tasks = [_aok(i) for i in range(3)]
        return await async_tools.gather_results(tasks)

    async def run_err():
        tasks = [_aok(1), _aerr("boom"), _aok(3)]
        return await async_tools.gather_results(tasks)

    assert asyncio.run(run_ok()) == result.Ok([0, 1, 2])
    assert asyncio.run(run_err()) == result.Err("boom")


def test_gather_results_accumulate():
    async def run_acc():
        tasks = [_aerr("a"), _aok(1), _aerr("b")]
        return await async_tools.gather_results_accumulate(tasks)

    assert asyncio.run(run_acc()) == result.Err(["a", "b"])
