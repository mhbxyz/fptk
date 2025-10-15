"""Benchmarks for ADT operations."""

from typing import Any

import pytest

from fptk.adt.option import NOTHING, Some
from fptk.adt.result import Err, Ok


@pytest.mark.benchmark
def test_option_map_some(benchmark: Any) -> None:
    opt = Some(42)
    benchmark(lambda: opt.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_option_map_nothing(benchmark: Any) -> None:
    benchmark(lambda: NOTHING.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_option_bind_some(benchmark: Any) -> None:
    opt = Some(42)
    benchmark(lambda: opt.bind(lambda x: Some(x + 1)))


@pytest.mark.benchmark
def test_option_bind_nothing(benchmark: Any) -> None:
    benchmark(lambda: NOTHING.bind(lambda x: Some(x + 1)))


@pytest.mark.benchmark
def test_result_map_ok(benchmark: Any) -> None:
    res = Ok(42)
    benchmark(lambda: res.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_result_map_err(benchmark: Any) -> None:
    res = Err("error")
    benchmark(lambda: res.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_result_bind_ok(benchmark: Any) -> None:
    res = Ok(42)
    benchmark(lambda: res.bind(lambda x: Ok(x + 1)))


@pytest.mark.benchmark
def test_result_bind_err(benchmark: Any) -> None:
    res = Err("error")
    benchmark(lambda: res.bind(lambda x: Ok(x + 1)))
