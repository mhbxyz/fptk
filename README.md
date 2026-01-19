<p align="center">
  <img src="docs/assets/fptk-logo.svg" alt="fptk" width="400">
</p>

<p align="center">
  <strong>Pragmatic functional programming for Python 3.13+</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fptk/"><img src="https://img.shields.io/pypi/v/fptk?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/fptk/"><img src="https://img.shields.io/pypi/pyversions/fptk" alt="Python"></a>
  <a href="https://github.com/mhbxyz/fptk/actions/workflows/ci.yml"><img src="https://github.com/mhbxyz/fptk/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/mhbxyz/fptk/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mhbxyz/fptk" alt="License"></a>
</p>

---

## Install

```bash
pip install fptk
```

## Quick Example

```python
from fptk.core.func import pipe
from fptk.adt.option import Some, NOTHING
from fptk.adt.result import Ok, Err

# Compose transformations
result = pipe(5, lambda x: x + 1, lambda x: x * 2)  # 12

# Handle absence explicitly
name = Some("alice").map(str.upper).unwrap_or("anonymous")  # "ALICE"

# Type-safe error handling
def parse(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"invalid: {s}")

parse("42").map(lambda x: x * 2)  # Ok(84)
```

## Documentation

**[mhbxyz.github.io/fptk](https://mhbxyz.github.io/fptk)**

## License

MIT
