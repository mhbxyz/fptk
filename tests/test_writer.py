from __future__ import annotations

from fptk.adt.writer import Writer, censor, listen, monoid_list, monoid_str, tell


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
