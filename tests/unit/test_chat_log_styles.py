"""Test _make_styles and _make_code_css use ThemeTokens, not hardcoded hex."""
from biome_fm.plugins.types import _DARK_FALLBACK
from biome_fm.views.theme import load_theme
from biome_fm.views._chat_log import _make_styles, _make_code_css


def test_dark_user_uses_surface2():
    s = _make_styles(_DARK_FALLBACK)
    assert _DARK_FALLBACK["surface2"] in s["user"][1]


def test_light_user_uses_surface2():
    light = load_theme("light")
    s = _make_styles(light)
    assert light["surface2"] in s["user"][1]


def test_dark_vs_light_differ():
    assert _make_styles(_DARK_FALLBACK) != _make_styles(load_theme("light"))


def test_error_uses_red_token():
    s = _make_styles(_DARK_FALLBACK)
    red = _DARK_FALLBACK["red"]  # e.g. "#ff453a"
    h = red.lstrip("#")
    expected_rgba = f"rgba({int(h[:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},0.15)"
    # error bg must be valid rgba(), not 8-digit hex unsupported by Qt HTML
    assert expected_rgba in s["error"][1]


def test_code_css_uses_surface():
    css = _make_code_css(_DARK_FALLBACK)
    assert _DARK_FALLBACK["surface"] in css
    assert _DARK_FALLBACK["border"] in css
    assert _DARK_FALLBACK["text_dim"] in css
