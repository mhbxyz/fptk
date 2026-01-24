from __future__ import annotations

from fptk.adt.writer import Monoid, Writer, censor, listen, monoid_list, monoid_str, tell


def test_writer_map_bind_run() -> None:
    # Test unit and map
    w = Writer.unit(5, monoid_list).map(lambda x: x + 1)
    assert w.run() == (6, [])

    # Test bind with log accumulation
    w2 = Writer.unit(3, monoid_list).bind(
        lambda x: tell([f"processed {x}"], monoid_list).map(lambda _: x * 2)
    )
    assert w2.run() == (6, ["processed 3"])

    # Test chaining
    w3 = Writer.unit(2, monoid_list).bind(
        lambda x: tell([f"step1: {x}"], monoid_list).bind(
            lambda _: tell([f"step2: {x}"], monoid_list).map(lambda _: x + 10)
        )
    )
    assert w3.run() == (12, ["step1: 2", "step2: 2"])


def test_tell_listen_censor() -> None:
    # tell adds to log
    w = tell(["log entry"], monoid_list)
    assert w.run() == (None, ["log entry"])

    # listen gets value and log
    w2 = listen(Writer.unit(42, monoid_list))
    assert w2.run() == ((42, []), [])

    # censor modifies log
    w3 = censor(lambda logs: [log.upper() for log in logs], tell(["hello"], monoid_list))
    assert w3.run() == (None, ["HELLO"])


def test_monoid_str() -> None:
    w = Writer.unit("a", monoid_str).bind(lambda x: tell("b", monoid_str).map(lambda _: x + "c"))
    assert w.run() == ("ac", "b")


def test_writer_repr() -> None:
    w = Writer.unit(1, monoid_list)
    assert "Writer" in repr(w)


ELEVEN = 11
FIFTEEN = 15
TEN = 10.0


def test_custom_monoid_sum() -> None:
    """Test Writer with sum monoid."""
    monoid_sum: Monoid[int] = Monoid(identity=0, combine=lambda a, b: a + b)

    w = (
        Writer.unit(5, monoid_sum)
        .bind(lambda x: tell(x, monoid_sum).map(lambda _: x * 2))
        .bind(lambda x: tell(x, monoid_sum).map(lambda _: x + 1))
    )

    value, log = w.run()
    assert value == ELEVEN
    assert log == FIFTEEN  # 5 + 10


def test_custom_monoid_max() -> None:
    """Test Writer with max monoid."""
    monoid_max: Monoid[float] = Monoid(identity=float("-inf"), combine=max)

    w = (
        tell(5.0, monoid_max)
        .bind(lambda _: tell(10.0, monoid_max))
        .bind(lambda _: tell(3.0, monoid_max))
    )

    _, log = w.run()
    assert log == TEN


def test_custom_monoid_set_union() -> None:
    """Test Writer with set union monoid."""
    monoid_set: Monoid[frozenset[str]] = Monoid(identity=frozenset(), combine=lambda a, b: a | b)

    w = (
        tell(frozenset({"a", "b"}), monoid_set)
        .bind(lambda _: tell(frozenset({"b", "c"}), monoid_set))
        .bind(lambda _: tell(frozenset({"d"}), monoid_set))
    )

    _, log = w.run()
    assert log == frozenset({"a", "b", "c", "d"})
