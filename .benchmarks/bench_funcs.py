"""Benchmarks for function combinators."""

import pytest

from fptk.core.func import compose, curry, identity, pipe


@pytest.mark.benchmark
def test_identity(benchmark):
    benchmark(lambda: identity(42))


@pytest.mark.benchmark
def test_pipe_3_functions(benchmark):
    def inc(x):
        return x + 1

    def double(x):
        return x * 2

    def square(x):
        return x * x

    benchmark(lambda: pipe(5, inc, double, square))


@pytest.mark.benchmark
def test_compose_3_functions(benchmark):
    def inc(x):
        return x + 1

    def double(x):
        return x * 2

    def square(x):
        return x * x

    composed = compose(compose(square, double), inc)
    benchmark(lambda: composed(5))


@pytest.mark.benchmark
def test_curry_simple(benchmark):
    def add(a, b):
        return a + b

    curried_add = curry(add)
    benchmark(lambda: curried_add(1)(2))


@pytest.mark.benchmark
def test_curry_complex(benchmark):
    def add4(a, b, c, d):
        return a + b + c + d

    curried_add4 = curry(add4)
    benchmark(lambda: curried_add4(1)(2)(3)(4))
