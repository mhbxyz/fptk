from __future__ import annotations

from typing import cast

from hypothesis import given
from hypothesis import strategies as st

from fptk.adt.option import NOTHING, Nothing, Option, Some
from fptk.adt.reader import Reader
from fptk.adt.result import Err, Ok, Result
from fptk.adt.state import State
from fptk.adt.traverse import traverse_option, traverse_result
from fptk.adt.writer import Writer, monoid_list

# ---------- Option Functor + Monad laws ----------


@st.composite
def options(draw) -> Some | Nothing:
    x = draw(st.integers())
    return Some(x) if draw(st.booleans()) else NOTHING


@given(options())
def test_option_functor_identity(opt: Option[int]) -> None:
    assert opt.map(lambda x: x) == opt


@given(options(), st.integers())
def test_option_functor_composition(opt: Option[int], k: int) -> None:
    def f(x: int) -> int:
        return x + 1

    def g(x: int) -> int:
        return x * (k % 5 + 1)

    lhs = opt.map(lambda x: f(g(x)))
    rhs = opt.map(g).map(f)
    assert lhs == rhs


def _of(x: int) -> Option[int]:
    return Some(x)


def _f(x: int) -> Option[int]:
    return Some(x + 1) if (x % 3) != 0 else cast(Option[int], NOTHING)


def _g(x: int) -> Option[int]:
    return Some(x * 2) if (x % 5) != 0 else cast(Option[int], NOTHING)


@given(st.integers())
def test_option_monad_left_identity(x: int) -> None:
    assert _of(x).bind(_f) == _f(x)


@given(options())
def test_option_monad_right_identity(m: Option[int]) -> None:
    assert m.bind(_of) == m


@given(options())
def test_option_monad_associativity(m: Option[int]) -> None:
    assert m.bind(_f).bind(_g) == m.bind(lambda x: _f(x).bind(_g))


# ---------- Result Functor + Monad laws ----------


@st.composite
def results(draw) -> Ok | Err:
    x = draw(st.integers())
    if draw(st.booleans()):
        return Ok(x)
    return Err("e")


@given(results())
def test_result_functor_identity(res: Result[int, str]) -> None:
    assert res.map(lambda x: x) == res


@given(results(), st.integers())
def test_result_functor_composition(res: Result[int, str], k: int) -> None:
    def f(x: int) -> int:
        return x + 1

    def g(x: int) -> int:
        return x * (k % 5 + 1)

    lhs = res.map(lambda x: f(g(x)))
    rhs = res.map(g).map(f)
    assert lhs == rhs


def of(x: int) -> Result[int, str]:
    return Ok(x)


def rf(x: int) -> Result[int, str]:
    return Ok(x + 1) if (x % 3) != 0 else Err("f")


def rg(x: int) -> Result[int, str]:
    return Ok(x * 2) if (x % 5) != 0 else Err("g")


@given(st.integers())
def test_result_monad_left_identity(x: int) -> None:
    assert of(x).bind(rf) == rf(x)


@given(results())
def test_result_monad_right_identity(m: Result[int, str]) -> None:
    if isinstance(m, Ok):
        assert m.bind(of) == of(m.value)
    else:
        assert m.bind(of) == m


@given(results())
def test_result_monad_associativity(m: Result[int, str]) -> None:
    assert m.bind(rf).bind(rg) == m.bind(lambda x: rf(x).bind(rg))


# ---------- Applicative Functor laws (for traverse) ----------


@given(st.lists(st.integers()))
def test_option_traverse_pure(xs: list[int]) -> None:
    """traverse(pure, xs) == pure(xs)"""

    def pure(x: int) -> Option[int]:
        return Some(x)

    result = traverse_option(xs, pure)
    expected = Some(xs)
    assert result == expected


@given(st.lists(options()))
def test_option_traverse_homomorphism(opts: list[Option[int]]) -> None:
    """traverse(f, xs) where f is pure should preserve structure"""

    def f(opt: Option[int]) -> Option[int]:
        return opt

    result = traverse_option(opts, f)
    expected = Some(
        [opt.value if isinstance(opt, Some) else None for opt in opts if isinstance(opt, Some)]
    )
    if any(isinstance(opt, Nothing) for opt in opts):
        expected = NOTHING
    assert result == expected


@given(st.lists(st.integers()))
def test_result_traverse_pure(xs: list[int]) -> None:
    """traverse(pure, xs) == pure(xs)"""

    def pure(x: int) -> Result[int, str]:
        return Ok(x)

    result = traverse_result(xs, pure)
    expected = Ok(xs)
    assert result == expected


@given(st.lists(results()))
def test_result_traverse_homomorphism(res_list: list[Result[int, str]]) -> None:
    """traverse(f, xs) where f is pure should preserve structure"""

    def f(res: Result[int, str]) -> Result[int, str]:
        return res

    result = traverse_result(res_list, f)
    values = []
    first_err = None
    for res in res_list:
        if isinstance(res, Ok):
            values.append(res.value)
        elif first_err is None and isinstance(res, Err):
            first_err = res.error

    if first_err is not None:
        expected = Err(first_err)
    else:
        expected = Ok(values)
    assert result == expected


# ---------- State Functor + Monad laws ----------


def state_of(x: int) -> State[int, int]:
    """Pure for State: return x without modifying state."""
    return State(lambda s: (x, s))


def state_f(x: int) -> State[int, int]:
    """Kleisli arrow: increment value and state."""
    return State(lambda s: (x + 1, s + 1))


def state_g(x: int) -> State[int, int]:
    """Kleisli arrow: double value, decrement state."""
    return State(lambda s: (x * 2, s - 1))


@given(st.integers(), st.integers())
def test_state_functor_identity(value: int, initial_state: int) -> None:
    """Functor identity: fmap id == id"""
    state: State[int, int] = State(lambda s: (value, s))
    assert state.map(lambda x: x).run(initial_state) == state.run(initial_state)


@given(st.integers(), st.integers(), st.integers())
def test_state_functor_composition(value: int, initial_state: int, k: int) -> None:
    """Functor composition: fmap (f . g) == fmap f . fmap g"""

    def f(x: int) -> int:
        return x + 1

    def g(x: int) -> int:
        return x * (k % 5 + 1)

    state: State[int, int] = State(lambda s: (value, s))
    lhs = state.map(lambda x: f(g(x))).run(initial_state)
    rhs = state.map(g).map(f).run(initial_state)
    assert lhs == rhs


@given(st.integers())
def test_state_monad_left_identity(x: int) -> None:
    """Left identity: return x >>= f == f x"""
    initial_state = 0
    assert state_of(x).bind(state_f).run(initial_state) == state_f(x).run(initial_state)


@given(st.integers(), st.integers())
def test_state_monad_right_identity(value: int, initial_state: int) -> None:
    """Right identity: m >>= return == m"""
    m: State[int, int] = State(lambda s: (value, s + 1))
    assert m.bind(state_of).run(initial_state) == m.run(initial_state)


@given(st.integers(), st.integers())
def test_state_monad_associativity(value: int, initial_state: int) -> None:
    """Associativity: (m >>= f) >>= g == m >>= (\\x -> f x >>= g)"""
    m: State[int, int] = State(lambda s: (value, s))
    lhs = m.bind(state_f).bind(state_g).run(initial_state)
    rhs = m.bind(lambda x: state_f(x).bind(state_g)).run(initial_state)
    assert lhs == rhs


# ---------- Reader Functor + Monad laws ----------


def reader_of(x: int) -> Reader[int, int]:
    """Pure for Reader: return x ignoring environment."""
    return Reader(lambda _: x)


def reader_f(x: int) -> Reader[int, int]:
    """Kleisli arrow: add environment to value."""
    return Reader(lambda env: x + env)


def reader_g(x: int) -> Reader[int, int]:
    """Kleisli arrow: multiply value by environment."""
    return Reader(lambda env: x * env)


@given(st.integers(), st.integers())
def test_reader_functor_identity(value: int, env: int) -> None:
    """Functor identity: fmap id == id"""
    reader: Reader[int, int] = Reader(lambda _: value)
    assert reader.map(lambda x: x).run(env) == reader.run(env)


@given(st.integers(), st.integers(), st.integers())
def test_reader_functor_composition(value: int, env: int, k: int) -> None:
    """Functor composition: fmap (f . g) == fmap f . fmap g"""

    def f(x: int) -> int:
        return x + 1

    def g(x: int) -> int:
        return x * (k % 5 + 1)

    reader: Reader[int, int] = Reader(lambda _: value)
    lhs = reader.map(lambda x: f(g(x))).run(env)
    rhs = reader.map(g).map(f).run(env)
    assert lhs == rhs


@given(st.integers(), st.integers())
def test_reader_monad_left_identity(x: int, env: int) -> None:
    """Left identity: return x >>= f == f x"""
    assert reader_of(x).bind(reader_f).run(env) == reader_f(x).run(env)


@given(st.integers(), st.integers())
def test_reader_monad_right_identity(value: int, env: int) -> None:
    """Right identity: m >>= return == m"""
    m: Reader[int, int] = Reader(lambda e: value + e)
    assert m.bind(reader_of).run(env) == m.run(env)


@given(st.integers(), st.integers())
def test_reader_monad_associativity(value: int, env: int) -> None:
    """Associativity: (m >>= f) >>= g == m >>= (\\x -> f x >>= g)"""
    m: Reader[int, int] = Reader(lambda _: value)
    lhs = m.bind(reader_f).bind(reader_g).run(env)
    rhs = m.bind(lambda x: reader_f(x).bind(reader_g)).run(env)
    assert lhs == rhs


# ---------- Writer Functor + Monad laws ----------


def writer_of(x: int) -> Writer[list[str], int]:
    """Pure for Writer: return x with empty log."""
    return Writer.unit(x, monoid_list)


def writer_f(x: int) -> Writer[list[str], int]:
    """Kleisli arrow: increment and log."""
    return Writer(x + 1, [f"f({x})"], monoid_list)  # pyright: ignore[reportArgumentType]


def writer_g(x: int) -> Writer[list[str], int]:
    """Kleisli arrow: double and log."""
    return Writer(x * 2, [f"g({x})"], monoid_list)  # pyright: ignore[reportArgumentType]


@given(st.integers())
def test_writer_functor_identity(value: int) -> None:
    """Functor identity: fmap id == id"""
    writer = Writer.unit(value, monoid_list)
    assert writer.map(lambda x: x).run() == writer.run()


@given(st.integers(), st.integers())
def test_writer_functor_composition(value: int, k: int) -> None:
    """Functor composition: fmap (f . g) == fmap f . fmap g"""

    def f(x: int) -> int:
        return x + 1

    def g(x: int) -> int:
        return x * (k % 5 + 1)

    writer = Writer.unit(value, monoid_list)
    lhs = writer.map(lambda x: f(g(x))).run()
    rhs = writer.map(g).map(f).run()
    assert lhs == rhs


@given(st.integers())
def test_writer_monad_left_identity(x: int) -> None:
    """Left identity: return x >>= f == f x"""
    assert writer_of(x).bind(writer_f).run() == writer_f(x).run()


@given(st.integers())
def test_writer_monad_right_identity(value: int) -> None:
    """Right identity: m >>= return == m"""
    m = Writer(value, ["initial"], monoid_list)  # pyright: ignore[reportArgumentType]
    assert m.bind(writer_of).run() == m.run()


@given(st.integers())
def test_writer_monad_associativity(value: int) -> None:
    """Associativity: (m >>= f) >>= g == m >>= (\\x -> f x >>= g)"""
    m = Writer.unit(value, monoid_list)
    lhs = m.bind(writer_f).bind(writer_g).run()
    rhs = m.bind(lambda x: writer_f(x).bind(writer_g)).run()
    assert lhs == rhs
