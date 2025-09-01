# fptk

Pragmatic functional programming helpers for Python (3.12+). Small, explicit API with useful building blocks: function combinators, lightweight ADTs, lazy iterators, and applicative validation.

## Features
- Tiny, explicit API (no magic or operator overloading)
- Ergonomic function helpers: `pipe`, `compose`, `curry`, `flip`, `tap`, `thunk`
- Lightweight ADTs: `Option`, `Result`, `NonEmptyList`
- Lazy iterator utilities: `map_iter`, `filter_iter`, `chunk`, `group_by_key`
- Applicative validation (`validate_all`) that accumulates all errors
- Strict typing (mypy --strict), clean style (ruff, black), and tests

## Install
```bash
pip install fptk

# Development install
pip install -e .[dev]
```

## Quick Start
```python
from fptk.core.func import pipe, compose, curry, tap
from fptk.adt.option import Some, NONE, from_nullable
from fptk.adt.result import Ok, Err
from fptk.adt.nelist import NonEmptyList
from fptk.iter.lazy import map_iter, filter_iter, chunk
from fptk.validate import validate_all

# Functions
assert pipe(2, lambda x: x + 1, lambda x: x * 3) == 9
inc_then_double = compose(lambda x: x * 2, lambda x: x + 1)
assert inc_then_double(3) == 8

# Option
assert Some(2).map(lambda x: x + 1).get_or(0) == 3
assert NONE.map(lambda x: x).get_or(42) == 42
assert list(Some("a").iter()) == ["a"]

# Result
assert Ok(2).map(lambda x: x + 1).is_ok()
assert Err("boom").map(lambda x: x).is_err()

# NonEmptyList
nel = NonEmptyList(1).append(2).append(3)
assert list(nel) == [1, 2, 3]

# Lazy iterators
assert list(map_iter(lambda x: x + 1, [1, 2, 3])) == [2, 3, 4]
assert list(filter_iter(lambda x: x % 2 == 0, [1, 2, 3, 4])) == [2, 4]
assert list(chunk([1, 2, 3, 4, 5], 2)) == [(1, 2), (3, 4), (5,)]

# Applicative validation
def min_len(n: int):
    def check(s: str):
        return Ok(s) if len(s) >= n else Err(f"len<{n}")
    return check

def has_digit(s: str):
    return Ok(s) if any(c.isdigit() for c in s) else Err("no digit")

assert validate_all([min_len(3), has_digit], "ab3").is_ok()
```

## API Overview
- `fptk.core.func`: `compose`, `pipe`, `curry`, `flip`, `tap`, `thunk`
- `fptk.adt.option`: `Option[T]`, `Some[T]`, `None_`, `NONE`, `from_nullable`
- `fptk.adt.result`: `Result[T, E]`, `Ok[T, E]`, `Err[T, E]`
- `fptk.adt.nelist`: `NonEmptyList[E]`
- `fptk.iter.lazy`: `map_iter`, `filter_iter`, `chunk`, `group_by_key`
- `fptk.validate`: `validate_all`

Public APIs are intentionally small; prefer explicit imports per module. See each module’s docstrings for usage details and examples.

## Development
This repo uses Makefile targets for common tasks:
- Install dev env: `make install-dev`
- Lint + types + tests: `make check`
- Tests: `make test` or verbose `make Test-verbose`
- Coverage: `make coverage`
- Lint/format: `make lint` / `make format`
- Build: `make build` / `make build-check`
- Pre-commit: `make precommit-install` / `make precommit-run`

Python 3.12+ is required. Type checking uses mypy `--strict` and code style uses ruff and black (line length 100).

## Contributing
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, ...)
- Run `make precommit-install` once; then `make precommit-run` locally
- Ensure `make check` passes before opening a PR

## Roadmap
The roadmap has moved to `docs/ROADMAP.md`.

## License
MIT — see `LICENSE`.
