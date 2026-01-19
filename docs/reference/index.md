# Reference

This reference documents every module, function, and type in fptk. Each page explains the underlying functional programming concepts, how the implementation works, and provides practical examples.

## Module Overview

### Core Functions

[`fptk.core.func`](core.md) — Function combinators for composing and transforming functions.

| Function | Purpose |
|----------|---------|
| `pipe` | Thread a value through functions left-to-right |
| `compose` | Combine functions right-to-left (mathematical notation) |
| `curry` | Transform multi-arg functions into chains of single-arg functions |
| `flip` | Swap the first two arguments of a function |
| `tap` | Execute side effects without breaking data flow |
| `thunk` | Lazy, memoized computation |
| `identity` | Return input unchanged |
| `const` | Ignore arguments, always return the same value |
| `once` | Run a function at most once |
| `try_catch` | Convert exceptions to Result values |

### Algebraic Data Types

These types model common patterns in a type-safe, composable way.

| Type | Module | Purpose |
|------|--------|---------|
| [`Option`](option.md) | `fptk.adt.option` | Explicit absence handling (replaces `None` checks) |
| [`Result`](result.md) | `fptk.adt.result` | Typed error handling (replaces exceptions) |
| [`Reader`](reader.md) | `fptk.adt.reader` | Dependency injection via environment threading |
| [`State`](state.md) | `fptk.adt.state` | Pure stateful computations |
| [`Writer`](writer.md) | `fptk.adt.writer` | Log accumulation alongside computation |
| [`NonEmptyList`](nelist.md) | `fptk.adt.nelist` | Lists guaranteed to have at least one element |

### Operations on Collections

| Module | Purpose |
|--------|---------|
| [`traverse`](traverse.md) | Sequence and traverse for Option/Result collections |
| [`validate`](validate.md) | Applicative validation (accumulate all errors) |
| [`lazy`](lazy.md) | Memory-efficient lazy iterator operations |
| [`async`](async.md) | Async utilities for concurrent Result operations |

## How to Read These Pages

Each reference page follows a consistent structure:

1. **Concept** — What functional programming idea this implements and why it matters
2. **API** — Types, functions, and their signatures
3. **How It Works** — Implementation details and design decisions
4. **Examples** — Practical code showing common usage patterns
5. **When to Use** — Guidance on appropriate use cases

## Quick Links by Use Case

**"I want to handle missing values without None checks"**
→ [`Option`](option.md)

**"I want typed errors instead of exceptions"**
→ [`Result`](result.md)

**"I want to chain transformations cleanly"**
→ [`pipe`, `compose`](core.md)

**"I want dependency injection without passing config everywhere"**
→ [`Reader`](reader.md)

**"I want to track state changes purely"**
→ [`State`](state.md)

**"I want to accumulate logs during computation"**
→ [`Writer`](writer.md)

**"I want to validate and collect all errors"**
→ [`validate_all`](validate.md)

**"I want to process large data without loading it all in memory"**
→ [`lazy iterators`](lazy.md)

**"I want to run async operations and combine their results"**
→ [`async tools`](async.md)
