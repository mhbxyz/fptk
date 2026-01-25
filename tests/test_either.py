from __future__ import annotations

from fptk.adt.either import Either, Left, Right

TWO = 2
THREE = 3
FOUR = 4
FIVE = 5
TEN = 10
ELEVEN = 11
TWENTY = 20
ONE_TWO_THREE = 123


def test_either_is_left_is_right() -> None:
    """Test is_left and is_right predicates."""
    assert Left(1).is_left() is True
    assert Left(1).is_right() is False

    assert Right("a").is_right() is True
    assert Right("a").is_left() is False


def test_either_map_left() -> None:
    """map_left transforms Left, passes through Right."""
    assert Left(FIVE).map_left(lambda x: x * TWO) == Left(TEN)
    assert Right("hello").map_left(lambda x: x * TWO) == Right("hello")


def test_either_map_right() -> None:
    """map_right transforms Right, passes through Left."""
    assert Right("hello").map_right(str.upper) == Right("HELLO")
    assert Left(FIVE).map_right(str.upper) == Left(FIVE)


def test_either_bimap() -> None:
    """bimap transforms both sides."""
    left: Either[int, str] = Left(TWO)
    right: Either[int, str] = Right("a")

    assert left.bimap(lambda x: x + 1, str.upper) == Left(THREE)
    assert right.bimap(lambda x: x + 1, str.upper) == Right("A")


def test_either_fold() -> None:
    """fold pattern matches to produce a single result."""
    left: Either[int, str] = Left(TEN)
    right: Either[int, str] = Right("hello")

    assert left.fold(lambda x: x * TWO, lambda s: len(s)) == TWENTY
    assert right.fold(lambda x: x * TWO, lambda s: len(s)) == FIVE


def test_either_swap() -> None:
    """swap flips Left to Right and vice versa."""
    assert Left(1).swap() == Right(1)
    assert Right("a").swap() == Left("a")

    # Double swap returns to original
    left: Either[int, str] = Left(FIVE)
    assert left.swap().swap() == left


def test_either_repr() -> None:
    """Test repr output."""
    assert repr(Left(THREE)) == "Left(3)"
    assert repr(Right("hello")) == "Right('hello')"


def test_either_equality() -> None:
    """Test equality comparison."""
    assert Left(1) == Left(1)
    assert Right("a") == Right("a")
    assert Left(1) != Left(TWO)
    assert Right("a") != Right("b")
    assert Left(1) != Right(1)


def test_either_hashable() -> None:
    """Either values are hashable."""
    s = {Left(1), Left(TWO), Right("a")}
    assert len(s) == THREE
    assert Left(1) in s
    assert Right("a") in s


def test_either_chaining() -> None:
    """Test chaining multiple transformations."""
    result = Left(FIVE).map_left(lambda x: x * TWO).map_left(lambda x: x + 1).map_right(str.upper)
    assert result == Left(ELEVEN)

    result2 = (
        Right("hello").map_left(lambda x: x * TWO).map_right(str.upper).map_right(lambda s: s + "!")
    )
    assert result2 == Right("HELLO!")


def test_either_use_case_parse_id() -> None:
    """Test typical use case: parsing that can return different types."""

    def parse_id(s: str) -> Either[int, str]:
        if s.isdigit():
            return Left(int(s))
        return Right(s)

    assert parse_id("123").is_left()
    assert parse_id("123").fold(lambda x: x, lambda s: -1) == ONE_TWO_THREE

    assert parse_id("abc").is_right()
    assert parse_id("abc").fold(lambda x: str(x), lambda s: s) == "abc"
