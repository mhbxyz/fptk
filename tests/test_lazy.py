from __future__ import annotations

from fptk.iter.lazy import chunk, filter_iter, group_by_key, map_iter


def test_map_filter_chunk() -> None:
    xs = [1, 2, 3, 4, 5]
    assert list(map_iter(lambda x: x * 2, xs)) == [2, 4, 6, 8, 10]
    assert list(filter_iter(lambda x: x % 2 == 0, xs)) == [2, 4]
    assert list(chunk(xs, 2)) == [(1, 2), (3, 4), (5,)]


def test_group_by_key_requires_sorted() -> None:
    xs = sorted(["aa", "b", "ccc", "dd"], key=len)
    groups = list(group_by_key(xs, key=len))
    assert groups == [(1, ["b"]), (2, ["aa", "dd"]), (3, ["ccc"])]
