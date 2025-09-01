from __future__ import annotations

from collections.abc import Callable

from fptk.adt.result import Err, Ok, Result
from fptk.validate import validate_all


def test_validate_all_accumulates() -> None:
    def len_at_least(n: int) -> Callable[[str], Result[str, str]]:
        def check(s: str) -> Result[str, str]:
            return Ok(s) if len(s) >= n else Err(f"len<{n}")

        return check

    def has_digit(s: str) -> Result[str, str]:
        return Ok(s) if any(c.isdigit() for c in s) else Err("no digit")

    r1 = validate_all([len_at_least(8), has_digit], "abc")
    assert r1.is_err()

    r2 = validate_all([len_at_least(3), has_digit], "ab3")
    assert r2.is_ok()
