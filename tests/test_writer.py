from __future__ import annotations

from fptk.adt.writer import (
    Monoid,
    Writer,
    censor,
    listen,
    monoid_all,
    monoid_any,
    monoid_list,
    monoid_max,
    monoid_min,
    monoid_product,
    monoid_set,
    monoid_str,
    monoid_sum,
    tell,
)


def test_writer_map_bind_run() -> None:
    # Test unit and map
    w = Writer.unit(5, monoid_list).map(lambda x: x + 1)
    assert w.run() == (6, [])

    # Test bind with log accumulation
    w2 = Writer.unit(3, monoid_list).bind(
        lambda x: tell([f"processed {x}"], monoid_list).map(  # pyright: ignore[reportArgumentType]
            lambda _: x * 2
        )
    )
    assert w2.run() == (6, ["processed 3"])

    # Test chaining
    w3 = Writer.unit(2, monoid_list).bind(
        lambda x: tell([f"step1: {x}"], monoid_list).bind(  # pyright: ignore[reportArgumentType]
            lambda _: tell([f"step2: {x}"], monoid_list).map(  # pyright: ignore[reportArgumentType]
                lambda _: x + 10
            )
        )
    )
    assert w3.run() == (12, ["step1: 2", "step2: 2"])


def test_tell_listen_censor() -> None:
    # tell adds to log
    w = tell(["log entry"], monoid_list)  # pyright: ignore[reportArgumentType]
    assert w.run() == (None, ["log entry"])

    # listen gets value and log
    w2 = listen(Writer.unit(42, monoid_list))
    assert w2.run() == ((42, []), [])

    # censor modifies log
    w3 = censor(
        lambda logs: [log.upper() for log in logs],
        tell(["hello"], monoid_list),  # pyright: ignore[reportArgumentType]
    )
    assert w3.run() == (None, ["HELLO"])


def test_monoid_str() -> None:
    w = Writer.unit("a", monoid_str).bind(lambda x: tell("b", monoid_str).map(lambda _: x + "c"))
    assert w.run() == ("ac", "b")


def test_writer_repr() -> None:
    w = Writer.unit(1, monoid_list)
    assert "Writer" in repr(w)


THREE = 3
FOUR = 4
FIVE = 5
FIVE_F = 5.0
SIX = 6
ELEVEN = 11
FIFTEEN = 15
TEN = 10.0
THREE_F = 3.0


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


# --- Tests for predefined monoids ---


def test_monoid_sum() -> None:
    """Test predefined sum monoid."""
    w = (
        Writer.unit(1, monoid_sum)
        .bind(
            lambda x: tell(x, monoid_sum).map(lambda _: x + 1)
        )  # pyright: ignore[reportArgumentType]
        .bind(
            lambda x: tell(x, monoid_sum).map(lambda _: x + 1)
        )  # pyright: ignore[reportArgumentType]
    )
    value, log = w.run()
    assert value == THREE
    assert log == THREE  # 1 + 2


def test_monoid_product() -> None:
    """Test predefined product monoid."""
    w = (
        Writer.unit(2, monoid_product)
        .bind(
            lambda x: tell(x, monoid_product).map(lambda _: x + 1)
        )  # pyright: ignore[reportArgumentType]
        .bind(
            lambda x: tell(x, monoid_product).map(lambda _: x + 1)
        )  # pyright: ignore[reportArgumentType]
    )
    value, log = w.run()
    assert value == FOUR
    assert log == SIX  # 2 * 3


def test_monoid_all() -> None:
    """Test predefined all (conjunction) monoid."""
    # All True
    w1 = tell(True, monoid_all).bind(lambda _: tell(True, monoid_all))
    _, log1 = w1.run()
    assert log1 is True

    # One False
    w2 = tell(True, monoid_all).bind(lambda _: tell(False, monoid_all))
    _, log2 = w2.run()
    assert log2 is False


def test_monoid_any() -> None:
    """Test predefined any (disjunction) monoid."""
    # All False
    w1 = tell(False, monoid_any).bind(lambda _: tell(False, monoid_any))
    _, log1 = w1.run()
    assert log1 is False

    # One True
    w2 = tell(False, monoid_any).bind(lambda _: tell(True, monoid_any))
    _, log2 = w2.run()
    assert log2 is True


def test_monoid_set_predefined() -> None:
    """Test predefined set union monoid."""
    w = tell(frozenset({"a", "b"}), monoid_set).bind(  # pyright: ignore[reportArgumentType]
        lambda _: tell(frozenset({"b", "c"}), monoid_set)
    )  # pyright: ignore[reportArgumentType]
    _, log = w.run()
    assert log == frozenset({"a", "b", "c"})


def test_monoid_max_predefined() -> None:
    """Test predefined max monoid."""
    w = (
        tell(FIVE_F, monoid_max)
        .bind(lambda _: tell(TEN, monoid_max))
        .bind(lambda _: tell(THREE_F, monoid_max))
    )
    _, log = w.run()
    assert log == TEN


def test_monoid_min_predefined() -> None:
    """Test predefined min monoid."""
    w = (
        tell(FIVE_F, monoid_min)
        .bind(lambda _: tell(TEN, monoid_min))
        .bind(lambda _: tell(THREE_F, monoid_min))
    )
    _, log = w.run()
    assert log == THREE_F


def test_monoid_identities() -> None:
    """Test that monoid identities work correctly."""
    # Sum identity is 0
    assert monoid_sum.identity == 0
    assert monoid_sum.combine(FIVE, monoid_sum.identity) == FIVE

    # Product identity is 1
    assert monoid_product.identity == 1
    assert monoid_product.combine(FIVE, monoid_product.identity) == FIVE

    # All identity is True
    assert monoid_all.identity is True
    assert monoid_all.combine(False, monoid_all.identity) is False

    # Any identity is False
    assert monoid_any.identity is False
    assert monoid_any.combine(True, monoid_any.identity) is True

    # Set identity is empty frozenset
    assert monoid_set.identity == frozenset()

    # Max identity is -inf
    assert monoid_max.identity == float("-inf")
    assert monoid_max.combine(FIVE_F, monoid_max.identity) == FIVE_F

    # Min identity is +inf
    assert monoid_min.identity == float("inf")
    assert monoid_min.combine(FIVE_F, monoid_min.identity) == FIVE_F
