"""Unit tests for F307 — High Contrast Theme (WCAG AAA)."""
from biome_fm.views.theme import load_theme

_REQUIRED = {"base", "surface", "surface2", "border", "text", "text_dim",
             "accent", "accent2", "red", "green"}


def test_high_contrast_toml_loads():
    tokens = load_theme("high-contrast")
    assert tokens["text"] == "#FFFFFF"
    assert tokens["base"] == "#000000"
    assert tokens["accent"] == "#FFFF00"


def test_inherits_dark():
    tokens = load_theme("high-contrast")
    assert set(tokens.keys()) >= _REQUIRED
