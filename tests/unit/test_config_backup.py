"""Unit tests for _rotate_config_backup — pure stdlib, no Qt."""
from pathlib import Path
import pytest
from biome_fm.config import _rotate_config_backup


def test_backup_created_on_save(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('theme = "dark"\n')
    _rotate_config_backup(cfg)
    assert len(list(tmp_path.glob("config.bak.*"))) == 1


def test_max_7_backups(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    cfg.write_text('theme = "dark"\n')
    t = [1000]

    def _tick():
        t[0] += 1
        return float(t[0])

    monkeypatch.setattr("biome_fm.config.time.time", _tick)
    for _ in range(10):
        _rotate_config_backup(cfg)
    assert len(list(tmp_path.glob("config.bak.*"))) == 7


def test_oldest_backup_evicted(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    for i in range(7):
        (tmp_path / f"config.bak.{1000 + i}").write_text(f"v{i}")
    cfg.write_text("current")
    monkeypatch.setattr("biome_fm.config.time.time", lambda: 9999.0)
    _rotate_config_backup(cfg)
    assert not (tmp_path / "config.bak.1000").exists()   # oldest gone
    assert (tmp_path / "config.bak.1006").exists()        # newest kept
    assert len(list(tmp_path.glob("config.bak.*"))) == 7


def test_no_config_no_backup(tmp_path):
    cfg = tmp_path / "config.toml"
    _rotate_config_backup(cfg)  # must not raise
    assert list(tmp_path.glob("config.bak.*")) == []


def test_backup_content_matches(tmp_path):
    cfg = tmp_path / "config.toml"
    content = 'theme = "light"\n'
    cfg.write_text(content)
    _rotate_config_backup(cfg)
    backup = next(tmp_path.glob("config.bak.*"))
    assert backup.read_text() == content
