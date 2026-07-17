"""Test recent_dirs tracking logic."""
from __future__ import annotations

from pathlib import Path

from biome_fm.app import _update_recent_dirs
from biome_fm.config import Config


def test_recent_dir_added_on_navigate():
    cfg = Config()
    _update_recent_dirs(cfg, Path("/home/user/docs"))
    assert "/home/user/docs" in cfg.recent_dirs


def test_recent_dir_dedup():
    cfg = Config()
    _update_recent_dirs(cfg, Path("/home/user/docs"))
    _update_recent_dirs(cfg, Path("/home/user/docs"))
    assert cfg.recent_dirs.count("/home/user/docs") == 1


def test_recent_dir_most_recent_first():
    cfg = Config()
    _update_recent_dirs(cfg, Path("/a"))
    _update_recent_dirs(cfg, Path("/b"))
    assert cfg.recent_dirs[0] == "/b"
    assert cfg.recent_dirs[1] == "/a"


def test_recent_dir_max_50():
    cfg = Config()
    for i in range(55):
        _update_recent_dirs(cfg, Path(f"/dir/{i}"))
    assert len(cfg.recent_dirs) == 50
