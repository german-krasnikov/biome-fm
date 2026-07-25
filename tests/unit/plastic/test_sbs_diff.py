"""Unit tests for _split_unified_diff — pure string parsing, no Qt needed."""
from __future__ import annotations

from biome_fm.plastic._components import _split_unified_diff


def test_split_context_lines():
    left, right = _split_unified_diff(" context line\n")
    assert left == ["context line"]
    assert right == ["context line"]


def test_split_added_only():
    left, right = _split_unified_diff("+added line\n")
    assert left == [""]
    assert right == ["added line"]


def test_split_removed_only():
    left, right = _split_unified_diff("-removed line\n")
    assert left == ["removed line"]
    assert right == [""]


def test_split_mixed():
    left, right = _split_unified_diff(" ctx\n-old\n+new\n ctx2\n")
    assert left == ["ctx", "old", "", "ctx2"]
    assert right == ["ctx", "", "new", "ctx2"]


def test_split_skips_headers():
    diff = "--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,3 @@\n ctx\n"
    left, right = _split_unified_diff(diff)
    assert left == ["ctx"]
    assert right == ["ctx"]


def test_split_empty():
    left, right = _split_unified_diff("")
    assert left == []
    assert right == []


def test_split_binary_message():
    left, right = _split_unified_diff("Binary files a.bin and b.bin differ\n")
    assert left == right == ["Binary files a.bin and b.bin differ"]
