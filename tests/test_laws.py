from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from fptk.adt.option import NOTHING, Nothing, Option, Some
from fptk.adt.result import Err, Ok, Result
from fptk.adt.traverse import traverse_option, traverse_result

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
    return Some(x + 1) if (x % 3) != 0 else NOTHING


def _g(x: int) -> Option[int]:
    return Some(x * 2) if (x % 5) != 0 else NOTHING


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
    assert m.bind(of) == m if isinstance(m, Err) else of(m.value)


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
        elif first_err is None:
            first_err = res.error

    if first_err is not None:
        expected = Err(first_err)
    else:
        expected = Ok(values)
    assert result == expected
