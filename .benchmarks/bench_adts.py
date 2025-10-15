"""Benchmarks for ADT operations."""

import pytest

from fptk.adt.option import NOTHING, Some
from fptk.adt.result import Err, Ok


@pytest.mark.benchmark
def test_option_map_some(benchmark):
    opt = Some(42)
    benchmark(lambda: opt.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_option_map_nothing(benchmark):
    benchmark(lambda: NOTHING.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_option_bind_some(benchmark):
    opt = Some(42)
    benchmark(lambda: opt.bind(lambda x: Some(x + 1)))


@pytest.mark.benchmark
def test_option_bind_nothing(benchmark):
    benchmark(lambda: NOTHING.bind(lambda x: Some(x + 1)))


@pytest.mark.benchmark
def test_result_map_ok(benchmark):
    res = Ok(42)
    benchmark(lambda: res.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_result_map_err(benchmark):
    res = Err("error")
    benchmark(lambda: res.map(lambda x: x + 1))


@pytest.mark.benchmark
def test_result_bind_ok(benchmark):
    res = Ok(42)
    benchmark(lambda: res.bind(lambda x: Ok(x + 1)))


@pytest.mark.benchmark
def test_result_bind_err(benchmark):
    res = Err("error")
    benchmark(lambda: res.bind(lambda x: Ok(x + 1)))
