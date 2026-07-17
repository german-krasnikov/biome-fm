"""TDD: layout profiles on Config."""
from __future__ import annotations

from pathlib import Path

from biome_fm.config import Config, load_config, save_config


def test_save_load_roundtrip(tmp_path: Path) -> None:
    cfg = Config()
    cfg.save_layout("dev", {"tree_visible": True, "preview_visible": True})
    cfg.save_layout("minimal", {"tree_visible": False, "preview_visible": False})

    p = tmp_path / "cfg.toml"
    save_config(cfg, p)
    cfg2 = load_config(p)

    assert cfg2.load_layout("dev") == {"tree_visible": True, "preview_visible": True}
    assert cfg2.load_layout("minimal") == {"tree_visible": False, "preview_visible": False}


def test_unknown_profile_returns_none() -> None:
    cfg = Config()
    assert cfg.load_layout("nonexistent") is None
