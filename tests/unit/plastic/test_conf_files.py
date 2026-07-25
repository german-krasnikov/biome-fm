"""Unit tests for _conf_files — read_conf / write_conf helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.plastic._conf_files import (
    cloaked_conf_path,
    ignore_conf_path,
    read_conf,
    write_conf,
)


def test_read_conf_missing_returns_empty(tmp_path):
    assert read_conf(tmp_path / "no.conf") == ""


def test_write_read_roundtrip(tmp_path):
    p = tmp_path / ".plastic" / "ignore.conf"
    write_conf(p, "*.pyc\n*.log\n")
    assert read_conf(p) == "*.pyc\n*.log\n"


def test_write_conf_creates_parent_dirs(tmp_path):
    p = tmp_path / "deep" / "nested" / "ignore.conf"
    write_conf(p, "*.tmp\n")
    assert p.exists()


def test_ignore_conf_path(tmp_path):
    assert ignore_conf_path(tmp_path) == tmp_path / ".plastic" / "ignore.conf"


def test_cloaked_conf_path(tmp_path):
    assert cloaked_conf_path(tmp_path) == tmp_path / ".plastic" / "cloaked.conf"
