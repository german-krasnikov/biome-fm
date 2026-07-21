"""Tests for system_index_search and SearchScope.SYSTEM_INDEX (F403)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.presenters.search_presenter import SearchScope, system_index_search


def _mock_run(stdout: str):
    def _run(*args, **kwargs):
        r = MagicMock()
        r.stdout = stdout
        return r
    return _run


def test_search_scope_has_system_index():
    assert SearchScope.SYSTEM_INDEX.value == "system_index"


def test_system_index_search_darwin(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("subprocess.run", _mock_run("/Users/foo/bar.txt\n/Users/foo/baz.txt\n"))
    result = system_index_search("foo")
    assert result == [Path("/Users/foo/bar.txt"), Path("/Users/foo/baz.txt")]


def test_system_index_search_with_root(monkeypatch):
    calls = []

    def capturing_run(*args, **kwargs):
        calls.append(args[0])
        r = MagicMock()
        r.stdout = "/Users/foo/bar.txt\n"
        return r

    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("subprocess.run", capturing_run)
    system_index_search("foo", root=Path("/Users/foo"))
    assert "-onlyin" in calls[0]
    assert "/Users/foo" in calls[0]


def test_system_index_search_timeout(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired("mdfind", 5)),
    )
    assert system_index_search("foo") == []


def test_system_index_search_no_binary(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()),
    )
    assert system_index_search("foo") == []
