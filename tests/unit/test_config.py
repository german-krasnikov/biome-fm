"""Tests for config.py — TOML persistence."""
from __future__ import annotations

from pathlib import Path

from biome_fm.config import Config, load_config, save_config


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg == Config()


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(theme="light"), p)
    assert load_config(p).theme == "light"


def test_partial_toml_merges_defaults(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text('theme = "solarized"\n', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.theme == "solarized"
    assert cfg.splitter_sizes == [600, 600]
    assert cfg.recent_dirs == []


def test_invalid_toml_returns_defaults(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text("not = valid = toml !!!\n", encoding="utf-8")
    assert load_config(p) == Config()


def test_splitter_sizes_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(splitter_sizes=[400, 800]), p)
    assert load_config(p).splitter_sizes == [400, 800]


def test_recent_dirs_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    save_config(Config(recent_dirs=["/home/user", "/tmp"]), p)
    assert load_config(p).recent_dirs == ["/home/user", "/tmp"]


def test_unknown_keys_ignored(tmp_path: Path) -> None:
    p = tmp_path / "cfg.toml"
    p.write_text('theme = "dark"\nfuture_key = "ignored"\n', encoding="utf-8")
    cfg = load_config(p)
    assert cfg.theme == "dark"
    assert not hasattr(cfg, "future_key")


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    p = tmp_path / "nested" / "deep" / "cfg.toml"
    save_config(Config(), p)
    assert p.exists()
