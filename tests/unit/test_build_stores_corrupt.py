"""STORES-03: guard _build_stores against corrupt store files (C23)."""
from __future__ import annotations

from pathlib import Path


def test_build_stores_with_corrupt_actions_json(tmp_path):
    """_build_stores must not raise when actions.json is corrupt."""
    from biome_fm.config import Config
    from biome_fm import app as _app

    (tmp_path / "actions.json").write_bytes(b"\xff[[")
    result = _app._build_stores(Config(), tmp_path)
    assert len(result) == 11


def test_safe_load_toml_corrupt_returns_default(tmp_path):
    """safe_load_toml returns default_factory() on corrupt TOML without raising."""
    from biome_fm.models._store_base import safe_load_toml

    toml_path = tmp_path / "bad.toml"
    toml_path.write_bytes(b"\xff[[")
    result = safe_load_toml(toml_path, lambda d: d["x"], lambda: "default")
    assert result == "default"
