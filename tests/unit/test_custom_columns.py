"""Unit tests for hidden_columns config field."""
from biome_fm.config import Config, load_config, save_config


def test_hidden_columns_default_empty():
    assert Config().hidden_columns == []


def test_hidden_columns_roundtrip(tmp_path):
    cfg = Config(hidden_columns=["Ext", "Size"])
    path = tmp_path / "config.toml"
    save_config(cfg, path)
    loaded = load_config(path)
    assert loaded.hidden_columns == ["Ext", "Size"]
