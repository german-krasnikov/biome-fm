"""Unit tests for shell cd-on-exit feature (F004)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from biome_fm.app import _write_last_dir


def test_writes_cwd_to_env_file(tmp_path, monkeypatch):
    dest = tmp_path / "last_dir"
    monkeypatch.setenv("BIOME_LAST_DIR_FILE", str(dest))
    _write_last_dir(Path("/some/path"))
    assert dest.read_text() == "/some/path"


def test_no_write_without_env_var(tmp_path, monkeypatch):
    monkeypatch.delenv("BIOME_LAST_DIR_FILE", raising=False)
    _write_last_dir(Path("/some/path"))  # must not raise, no file written
    # nothing to assert — just no crash and no file


def test_empty_path_not_written(tmp_path, monkeypatch):
    dest = tmp_path / "last_dir"
    monkeypatch.setenv("BIOME_LAST_DIR_FILE", str(dest))
    _write_last_dir(None)
    assert not dest.exists()


def test_overwrites_existing_file(tmp_path, monkeypatch):
    dest = tmp_path / "last_dir"
    dest.write_text("/old/path")
    monkeypatch.setenv("BIOME_LAST_DIR_FILE", str(dest))
    _write_last_dir(Path("/new/path"))
    assert dest.read_text() == "/new/path"


def test_vfs_path_not_written(tmp_path, monkeypatch):
    dest = tmp_path / "last_dir"
    monkeypatch.setenv("BIOME_LAST_DIR_FILE", str(dest))
    _write_last_dir(Path("sftp://host/some/path"))
    assert not dest.exists()


def test_oserror_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOME_LAST_DIR_FILE", str(tmp_path / "no" / "such" / "dir" / "f"))
    _write_last_dir(Path("/some/path"))  # must not raise
