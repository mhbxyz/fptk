# fptk

Pragmatic functional programming for Python 3.13+.

## Install

```bash
pip install fptk
```

## Features

- **Function combinators** — `pipe`, `compose`, `curry`, `flip`, `tap`, `once`
- **Option** — `Some`, `Nothing` for explicit absence
- **Result** — `Ok`, `Err` for typed error handling
- **Monads** — `Reader`, `State`, `Writer` for pure effects
- **Iterators** — `map_iter`, `filter_iter`, `chunk`, `group_by_key`
- **Validation** — `validate_all` accumulates all errors
- **Async** — `async_pipe`, `gather_results`, async traverse

Strict typing (`mypy --strict`), no magic, immutable ADTs.

## Quick Start

```python
from fptk.core.func import pipe, compose, curry
from fptk.adt.option import Some, NOTHING
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

# Pipe values through functions
result = pipe(5, lambda x: x + 1, lambda x: x * 2)  # 12

# Option for nullable values
name = Some("alice").map(str.upper).unwrap_or("anonymous")  # "ALICE"
missing = NOTHING.map(str.upper).unwrap_or("anonymous")     # "anonymous"

# Result for error handling
def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"invalid: {s}")

parse_int("42").map(lambda x: x * 2)  # Ok(84)
parse_int("xx").map(lambda x: x * 2)  # Err("invalid: xx")

# Validation accumulates all errors
def min_len(n: int):
    return lambda s: Ok(s) if len(s) >= n else Err(f"len<{n}")

def has_digit(s: str):
    return Ok(s) if any(c.isdigit() for c in s) else Err("no digit")

validate_all([min_len(3), has_digit], "ab")  # Err(["len<3", "no digit"])
validate_all([min_len(3), has_digit], "abc1")  # Ok("abc1")
```

## API

| Module | Exports |
|--------|---------|
| `fptk.core.func` | `pipe`, `compose`, `curry`, `flip`, `tap`, `thunk`, `once`, `identity`, `const`, `try_catch` |
| `fptk.adt.option` | `Option`, `Some`, `Nothing`, `NOTHING`, `from_nullable` |
| `fptk.adt.result` | `Result`, `Ok`, `Err` |
| `fptk.adt.nelist` | `NonEmptyList` |
| `fptk.adt.reader` | `Reader`, `ask`, `local` |
| `fptk.adt.state` | `State`, `get`, `put`, `modify`, `gets` |
| `fptk.adt.writer` | `Writer`, `tell`, `listen`, `censor` |
| `fptk.adt.traverse` | `sequence_option`, `traverse_option`, `sequence_result`, `traverse_result` |
| `fptk.iter.lazy` | `map_iter`, `filter_iter`, `chunk`, `group_by_key` |
| `fptk.validate` | `validate_all` |
| `fptk.async_tools` | `async_pipe`, `gather_results`, `gather_results_accumulate` |

## Development

```bash
make dev      # Install deps + pre-commit hooks
make check    # Lint + type + test
make ci       # Full CI pipeline
```

## License

MIT
