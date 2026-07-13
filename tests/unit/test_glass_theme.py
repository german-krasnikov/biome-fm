"""Unit tests for glass theme helpers. No Qt."""
from unittest.mock import MagicMock


def test_hex_to_rgba():
    from biome_fm.views.theme import _hex_to_rgba
    assert _hex_to_rgba("#1c1c1e", 178) == "rgba(28, 28, 30, 178)"


def test_hex_to_rgba_white():
    from biome_fm.views.theme import _hex_to_rgba
    assert _hex_to_rgba("#ffffff", 200) == "rgba(255, 255, 255, 200)"


def test_glass_only_transforms_background_tokens():
    from biome_fm.views.theme import _apply_glass_alpha
    tokens = {
        "base": "#1c1c1e", "surface": "#2c2c2e", "surface2": "#3a3a3c",
        "text": "#f5f5f7", "accent": "#0a84ff", "border": "#48484a",
        "text_dim": "#98989f", "accent2": "#5e5ce6", "red": "#ff453a", "green": "#32d74b",
    }
    result = _apply_glass_alpha(tokens)
    assert result["base_bg"] == "transparent"
    assert result["base"] == "#1c1c1e"  # base stays opaque (used as text color)
    assert result["surface"].startswith("rgba(")
    assert result["surface2"].startswith("rgba(")
    for key in ("text", "accent", "border", "text_dim", "accent2", "red", "green"):
        assert result[key].startswith("#"), f"{key} should remain hex"


def test_glass_does_not_mutate_original():
    from biome_fm.views.theme import _apply_glass_alpha
    tokens = {"base": "#1c1c1e", "surface": "#2c2c2e", "surface2": "#3a3a3c"}
    original = dict(tokens)
    _apply_glass_alpha(tokens)
    assert tokens == original


def test_hex_to_rgba_passthrough_non_hex():
    from biome_fm.views.theme import _hex_to_rgba
    assert _hex_to_rgba("rgba(10, 20, 30, 100)", 178) == "rgba(10, 20, 30, 100)"
    assert _hex_to_rgba("black", 178) == "black"


def test_config_glass_default_false():
    from biome_fm.config import Config
    assert Config().glass is False


def test_config_glass_roundtrip(tmp_path):
    from biome_fm.config import Config, load_config, save_config
    cfg = Config(glass=True)
    p = tmp_path / "config.toml"
    save_config(cfg, p)
    loaded = load_config(p)
    assert loaded.glass is True
