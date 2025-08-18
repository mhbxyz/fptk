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

## 🗺️ Roadmap & Implementation Plan

### Principles
- **Explicit over clever**: no operator overloading for core flows.
- **Errors as values**: prefer `Result` for control flow; exceptions reserved for truly exceptional cases.
- **Lazy by default** on iterables.
- **Strict typing** and property-based tests for algebraic laws.

### Milestone 0 — Bootstrap (v0.1.x)
- Repo skeleton, tooling, CI, release automation, packaging
- Minimal `core/func`, `Option`, `Result`, `NonEmptyList`, `lazy`, `validate_all`
- Unit tests for each module

**Acceptance**: CI green, `pip install -e .` works, `pytest` passes.

---

### Milestone 1 — Utilities & Niceties (v0.2.x)
- `core.func`: add `identity`, `const`, `once`, `try_catch(f) -> Result`
- `adt.option`: `to_result(err)`, `or_else`, `match` helper
- `adt.result`: `unwrap_or`, `unwrap_or_else`, `match` helper
- `sequence`/`traverse` for `Option` and `Result`
- Better `__repr__` for ADTs

**Tests**: property-based tests for functor/monad laws (Hypothesis).

**Docs**: examples showing `railway-oriented programming` patterns.

---

### Milestone 2 — Async & Concurrency (v0.3.x)
- `bind_async`/`map_async` variants for `Option`/`Result`
- `gather_results(tasks) -> Result[list[T], E]` (fail-fast vs accumulate strategy)
- `async_pipe` helper
- Benchmarks vs naive asyncio patterns

**Tests**: asyncio tests; ensure type inference stays sane.

---

### Milestone 3 — Readers & State (v0.4.x)
- `Reader[R, A]` for dependency injection
- `State[S, A]` for pure stateful workflows
- `Writer[W, A]` (monoidal log)
- Combinators and examples (configuration loading, validation + enrichment)

**Docs**: how to keep side effects at the edge; layering with `Result`.

---

### Milestone 4 — Transformers & Interop (v0.5.x)
- `OptionT`, `ResultT` transformers
- Interop helpers for popular libs (e.g., mapping Exceptions→`Err`)
- Optional `parse` combinators for text/HTTP inputs

**Perf**: micro-benchmarks, flamegraphs for hot paths.

---

### Milestone 5 — v1.0.0 (API freeze)
- Audit public surface; deprecate rough edges
- Documentation site with narrative guides and recipes
- Stability guarantee and semver promise

**Release criteria**: 100% typed, 95%+ unit coverage on core modules, clear migration notes from 0.x.
