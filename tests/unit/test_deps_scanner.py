"""TDD tests for deps_scanner.scan_cleanup_dirs."""
import threading
from pathlib import Path

import pytest

from biome_fm.models.deps_scanner import scan_cleanup_dirs


def test_scan_finds_node_modules(tmp_path):
    (tmp_path / "project" / "node_modules").mkdir(parents=True)
    (tmp_path / "project" / "src").mkdir(parents=True)
    result = scan_cleanup_dirs(tmp_path, threading.Event())
    assert result == [tmp_path / "project" / "node_modules"]


def test_scan_finds_multiple(tmp_path):
    for d in ("node_modules", "__pycache__", ".venv"):
        (tmp_path / d).mkdir()
    result = scan_cleanup_dirs(tmp_path, threading.Event())
    assert set(result) == {tmp_path / d for d in ("node_modules", "__pycache__", ".venv")}


def test_scan_respects_max_depth(tmp_path):
    # 7 levels deep: tmp/a/b/c/d/e/f/node_modules
    deep = tmp_path / "a" / "b" / "c" / "d" / "e" / "f"
    (deep / "node_modules").mkdir(parents=True)
    result = scan_cleanup_dirs(tmp_path, threading.Event(), max_depth=3)
    assert result == []


def test_scan_cancel(tmp_path):
    (tmp_path / "node_modules").mkdir()
    cancel = threading.Event()
    cancel.set()
    result = scan_cleanup_dirs(tmp_path, cancel)
    assert result == []


def test_scan_skips_non_cleanup_dirs(tmp_path):
    for d in ("src", "lib", "docs"):
        (tmp_path / d).mkdir()
    result = scan_cleanup_dirs(tmp_path, threading.Event())
    assert result == []
