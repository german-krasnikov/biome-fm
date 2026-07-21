"""Unit tests for Finder comment fallback (no Qt, no xattr)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.models.finder_tags import (
    _get_comment_fallback,
    _meta_path,
    _set_comment_fallback,
    get_finder_comment,
    set_finder_comment,
)


def test_comment_roundtrip_fallback(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("data")
    _set_comment_fallback(f, "hello world")
    assert _get_comment_fallback(f) == "hello world"


def test_comment_fallback_no_file(tmp_path: Path) -> None:
    f = tmp_path / "nonexistent.txt"
    assert _get_comment_fallback(f) == ""


def test_comment_fallback_preserves_other_keys(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("data")
    mp = _meta_path(f)
    mp.write_text(json.dumps({"other_key": "other_val"}))
    _set_comment_fallback(f, "my comment")
    data = json.loads(mp.read_text())
    assert data["comment"] == "my comment"
    assert data["other_key"] == "other_val"
