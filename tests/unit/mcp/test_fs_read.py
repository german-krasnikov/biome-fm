"""Unit tests for mcp/tools/fs_read.py — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.mcp.tools.fs_read import (
    _list_directory,
    _read_file,
    _search_files,
    _stat_item,
)
from biome_fm.models.vfs_router import VFSRouter


@pytest.fixture
def vfs() -> VFSRouter:
    return VFSRouter()


# --- list_directory ---

def test_list_directory_returns_items(tmp_path: Path, vfs: VFSRouter) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    result = _list_directory(str(tmp_path), vfs)
    names = {r["name"] for r in result}
    assert "a.txt" in names
    assert "sub" in names


def test_list_directory_empty(tmp_path: Path, vfs: VFSRouter) -> None:
    result = _list_directory(str(tmp_path), vfs)
    assert result == []


def test_list_directory_item_shape(tmp_path: Path, vfs: VFSRouter) -> None:
    (tmp_path / "f.txt").write_text("x")
    result = _list_directory(str(tmp_path), vfs)
    item = result[0]
    assert {"name", "is_dir", "size", "modified", "path"} <= item.keys()


# --- stat_item ---

def test_stat_item_file(tmp_path: Path, vfs: VFSRouter) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("world")
    result = _stat_item(str(f), vfs)
    assert result["name"] == "hello.txt"
    assert result["is_dir"] is False
    assert result["size"] == 5


def test_stat_item_directory(tmp_path: Path, vfs: VFSRouter) -> None:
    d = tmp_path / "mydir"
    d.mkdir()
    result = _stat_item(str(d), vfs)
    assert result["name"] == "mydir"
    assert result["is_dir"] is True


# --- read_file ---

def test_read_file_content(tmp_path: Path) -> None:
    f = tmp_path / "data.txt"
    f.write_text("hello world")
    result = _read_file(str(f))
    assert result["content"] == "hello world"
    assert result["truncated"] is False
    assert result["size"] == 11


def test_read_file_truncates(tmp_path: Path) -> None:
    f = tmp_path / "big.txt"
    f.write_bytes(b"x" * 200)
    result = _read_file(str(f), max_bytes=100)
    assert len(result["content"]) <= 100
    assert result["truncated"] is True


def test_read_file_binary_detection(tmp_path: Path) -> None:
    f = tmp_path / "img.bin"
    f.write_bytes(bytes(range(256)))
    result = _read_file(str(f))
    assert result["content"] == "[binary file]"


# --- search_files ---

def test_search_files_glob(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("")
    result = _search_files(str(tmp_path), "*.py")
    assert len(result) == 3


def test_search_files_no_match(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("")
    result = _search_files(str(tmp_path), "*.py")
    assert result == []


def test_search_files_non_recursive(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.py").write_text("")
    result = _search_files(str(tmp_path), "*.py", recursive=False)
    assert len(result) == 1
    assert result[0].endswith("a.py")
