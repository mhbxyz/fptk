"""Small lazy iterator helpers: map, filter, chunk, group_by_key.

These utilities compose well with Python iterables while remaining lazy where
possible.

- ``map_iter(f, xs)``: lazily map a transformation over items
- ``filter_iter(pred, xs)``: lazily filter items by a predicate
- ``chunk(xs, size)``: yield fixed-size tuples until exhaustion
- ``group_by_key(xs, key)``: group consecutive items by key (input must be sorted)

Examples:
    >>> from fptk.iter.lazy import map_iter, filter_iter, chunk, group_by_key
    >>> list(map_iter(lambda x: x + 1, [1, 2, 3]))
    [2, 3, 4]
    >>> list(filter_iter(lambda x: x % 2 == 0, [1, 2, 3, 4]))
    [2, 4]
    >>> list(chunk([1, 2, 3, 4, 5], 2))
    [(1, 2), (3, 4), (5,)]
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from itertools import groupby, islice
from typing import TypeVar

__all__ = [
    "map_iter",
    "filter_iter",
    "chunk",
    "group_by_key",
]

T = TypeVar("T")
K = TypeVar("K")


def map_iter[T, K](f: Callable[[T], K], xs: Iterable[T]) -> Iterator[K]:
    """Lazily apply ``f`` to each item of ``xs``.

    Equivalent to ``map(f, xs)`` but typed with explicit iterator output.
    """
    for x in xs:
        yield f(x)


def filter_iter[T](pred: Callable[[T], bool], xs: Iterable[T]) -> Iterator[T]:
    """Lazily yield items of ``xs`` for which ``pred(item)`` is true."""
    for x in xs:
        if pred(x):
            yield x


def chunk[T](xs: Iterable[T], size: int) -> Iterator[tuple[T, ...]]:
    """Yield tuples of up to ``size`` items from ``xs``.

    The final chunk may be shorter if items do not divide evenly. Preserves
    ``None`` values in the input.
    """
    it = iter(xs)
    while True:
        buf = tuple(islice(it, size))
        if not buf:
            return
        yield buf


def group_by_key[T, K](xs: Iterable[T], key: Callable[[T], K]) -> Iterator[tuple[K, list[T]]]:
    """Group consecutive items by ``key``; requires input pre-sorted by ``key``.

    Each group is realized as a list for convenience.
    """
    for k, grp in groupby(xs, key=key):
        yield k, list(grp)
