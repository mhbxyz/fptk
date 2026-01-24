from __future__ import annotations

from fptk.adt.state import State, get, gets, modify, put


def test_state_map_bind_run() -> None:
    # Test map
    s = get().map(lambda x: x + 1)
    assert s.run(5) == (6, 5)

    # Test bind
    s2 = get().bind(lambda x: put(x * 2).map(lambda _: x))
    assert s2.run(3) == (3, 6)

    # Test chaining
    s3 = get().bind(lambda x: modify(lambda y: y + 1).map(lambda _: x * 2))
    assert s3.run(4) == (8, 5)


def test_get_put_modify() -> None:
    # get returns current state
    assert get().run(42) == (42, 42)

    # put sets new state
    assert put(10).run(0) == (None, 10)

    # modify updates state
    assert modify(lambda x: x * 2).run(3) == (None, 6)


def test_gets() -> None:
    # gets extracts and transforms without changing state
    s = gets(lambda x: x + 10)
    assert s.run(5) == (15, 5)


def test_state_repr() -> None:
    s = get()
    assert "State" in repr(s)


def test_map_single_execution() -> None:
    """map() should only execute run_state once."""
    call_count = 0

    def counting_state(s: int) -> tuple[int, int]:
        nonlocal call_count
        call_count += 1
        return (s * 2, s + 1)

    state: State[int, int] = State(counting_state)
    result = state.map(lambda x: x + 10)

    call_count = 0
    result.run(5)
    assert call_count == 1


def test_bind_single_execution() -> None:
    """bind() should only execute run_state once."""
    call_count = 0

    def counting_state(s: int) -> tuple[int, int]:
        nonlocal call_count
        call_count += 1
        return (s * 2, s + 1)

    state: State[int, int] = State(counting_state)
    result = state.bind(lambda x: State(lambda s: (x + 10, s)))

    call_count = 0
    result.run(5)
    assert call_count == 1
