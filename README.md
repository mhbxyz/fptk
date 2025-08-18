# funktools

Pragmatic functional programming helpers for Python.

## Why
- Tiny, explicit API (no magic)
- Ergonomic primitives: `pipe`, `compose`, `curry`, `tap`
- Lightweight ADTs: `Option`, `Result`, `NonEmptyList`
- Lazy iterable combinators
- Applicative validation that *accumulates* errors

## Install
```bash
pip install funktools
# or for development
pip install -e .[dev]
```

## Contributing
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, ...)
- Run `pre-commit install` 
- `pytest -q` before PR
