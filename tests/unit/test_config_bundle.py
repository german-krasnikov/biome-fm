"""TDD: config import/export bundle."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.config import Config
from biome_fm.models.config_bundle import export_config, import_config


def test_export_import_roundtrip(tmp_path: Path) -> None:
    cfg = Config(theme="light", editor_cmd="vim")
    p = tmp_path / "bundle.toml"
    export_config(cfg, p)
    data = import_config(p)
    assert data["theme"] == "light"
    assert data["editor_cmd"] == "vim"


def test_invalid_toml_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.toml"
    p.write_text("not = valid = toml!!!", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid TOML"):
        import_config(p)
