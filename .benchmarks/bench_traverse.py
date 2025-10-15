"""Benchmarks for traverse operations."""

from typing import Any

import pytest

from fptk.adt.option import NOTHING, Some
from fptk.adt.result import Err, Ok
from fptk.adt.traverse import sequence_option, sequence_result, traverse_option, traverse_result

THREE = 3


@pytest.mark.benchmark
def test_sequence_option_success(benchmark: Any) -> None:
    opts = [Some(1), Some(2), Some(3), Some(4), Some(5)]
    benchmark(lambda: sequence_option(opts))


@pytest.mark.benchmark
def test_sequence_option_failure(benchmark: Any) -> None:
    opts = [Some(1), Some(2), NOTHING, Some(4), Some(5)]
    benchmark(lambda: sequence_option(opts))


@pytest.mark.benchmark
def test_traverse_option_success(benchmark: Any) -> None:
    xs = [1, 2, 3, 4, 5]
    benchmark(lambda: traverse_option(xs, lambda x: Some(x * 2)))


@pytest.mark.benchmark
def test_traverse_option_failure(benchmark: Any) -> None:
    xs = [1, 2, 3, 4, 5]
    benchmark(lambda: traverse_option(xs, lambda x: NOTHING if x == THREE else Some(x)))


@pytest.mark.benchmark
def test_sequence_result_success(benchmark: Any) -> None:
    results = [Ok(1), Ok(2), Ok(3), Ok(4), Ok(5)]
    benchmark(lambda: sequence_result(results))


@pytest.mark.benchmark
def test_sequence_result_failure(benchmark: Any) -> None:
    results = [Ok(1), Ok(2), Err("fail"), Ok(4), Ok(5)]
    benchmark(lambda: sequence_result(results))


@pytest.mark.benchmark
def test_traverse_result_success(benchmark: Any) -> None:
    xs = [1, 2, 3, 4, 5]
    benchmark(lambda: traverse_result(xs, lambda x: Ok(x * 2)))


@pytest.mark.benchmark
def test_traverse_result_failure(benchmark: Any) -> None:
    xs = [1, 2, 3, 4, 5]
    benchmark(lambda: traverse_result(xs, lambda x: Err("fail") if x == THREE else Ok(x)))
