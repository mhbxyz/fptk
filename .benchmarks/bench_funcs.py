"""Benchmarks for function combinators."""

from typing import Any

import pytest

from fptk.core.func import compose, curry, identity, pipe


@pytest.mark.benchmark
def test_identity(benchmark: Any) -> None:
    benchmark(lambda: identity(42))


@pytest.mark.benchmark
def test_pipe_3_functions(benchmark: Any) -> None:
    def inc(x: int) -> int:
        return x + 1

    def double(x: int) -> int:
        return x * 2

    def square(x: int) -> int:
        return x * x

    benchmark(lambda: pipe(5, inc, double, square))


@pytest.mark.benchmark
def test_compose_3_functions(benchmark: Any) -> None:
    def inc(x: int) -> int:
        return x + 1

    def double(x: int) -> int:
        return x * 2

    def square(x: int) -> int:
        return x * x

    composed = compose(compose(square, double), inc)
    benchmark(lambda: composed(5))


@pytest.mark.benchmark
def test_curry_simple(benchmark: Any) -> None:
    def add(a: int, b: int) -> int:
        return a + b

    curried_add = curry(add)
    benchmark(lambda: curried_add(1)(2))


@pytest.mark.benchmark
def test_curry_complex(benchmark: Any) -> None:
    def add4(a: int, b: int, c: int, d: int) -> int:
        return a + b + c + d

    curried_add4 = curry(add4)
    benchmark(lambda: curried_add4(1)(2)(3)(4))
