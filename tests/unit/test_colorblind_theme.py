"""Unit tests for F447 — Color-Blind Safe Theme Variant."""
import importlib.resources
import tomllib

from biome_fm.views.theme import load_theme


def _raw() -> dict:
    pkg = importlib.resources.files("biome_fm.themes")
    toml_bytes = (pkg / "colorblind-dark.toml").read_bytes()
    return tomllib.loads(toml_bytes.decode())


def test_colorblind_theme_loads():
    tokens = load_theme("colorblind-dark")
    assert tokens  # no KeyError / FileNotFoundError


def test_colorblind_inherits_from_dark():
    data = _raw()
    assert data["meta"]["inherits"] == "dark"


def test_colorblind_overrides_colors():
    dark = load_theme("dark")
    cb = load_theme("colorblind-dark")
    # At least red and green must be overridden to Okabe-Ito values
    assert cb["red"] != dark["red"]
    assert cb["green"] != dark["green"]


def test_no_red_green_in_colorblind():
    tokens = load_theme("colorblind-dark")
    values_lower = {v.lower() for v in tokens.values() if isinstance(v, str)}
    assert "#ff0000" not in values_lower
    assert "#00ff00" not in values_lower
