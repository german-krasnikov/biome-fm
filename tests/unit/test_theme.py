"""Unit tests for theme QSS generation — no Qt needed."""
import pytest

from biome_fm.views.theme import _QSS, _TOKENS


def test_all_tokens_substituted():
    qss = _QSS.substitute(_TOKENS)
    # No unresolved Template placeholders remain
    assert "$" not in qss


def test_macos_base_color_present():
    qss = _QSS.substitute(_TOKENS)
    assert _TOKENS["base"] in qss      # #1c1c1e
    assert _TOKENS["accent"] in qss    # #0a84ff


def test_key_selectors_present():
    qss = _QSS.substitute(_TOKENS)
    for selector in ("QTableView", "QLineEdit", "QPushButton", "QFrame#command-palette"):
        assert selector in qss, f"Missing selector: {selector}"


# ── New tests (Phase 1) ───────────────────────────────────────────────────────

_REQUIRED_TOKENS = {"base", "surface", "surface2", "border", "text", "text_dim",
                    "accent", "accent2", "red", "green"}


def test_dark_theme_loads_all_tokens():
    from biome_fm.views.theme import load_theme
    tokens = load_theme("dark")
    assert set(tokens.keys()) >= _REQUIRED_TOKENS


def test_light_theme_loads_all_tokens():
    from biome_fm.views.theme import load_theme
    tokens = load_theme("light")
    assert set(tokens.keys()) >= _REQUIRED_TOKENS


def test_catppuccin_mocha_loads_all_tokens():
    from biome_fm.views.theme import load_theme
    tokens = load_theme("catppuccin-mocha")
    assert set(tokens.keys()) >= _REQUIRED_TOKENS


def test_unknown_theme_falls_back_to_dark():
    from biome_fm.views.theme import _DARK_FALLBACK, load_theme
    tokens = load_theme("does-not-exist-xyz")
    assert tokens["base"] == _DARK_FALLBACK["base"]


@pytest.mark.parametrize("name", ["dark", "light", "catppuccin-mocha"])
def test_no_unresolved_tokens(name):
    from string import Template

    from biome_fm.views.theme import _QSS_TMPL, load_theme
    tokens = load_theme(name)
    qss = Template(_QSS_TMPL).substitute(tokens)
    assert "$" not in qss


def test_light_is_brighter_than_dark():
    from biome_fm.views.theme import load_theme
    dark = load_theme("dark")
    light = load_theme("light")
    assert light["base"].lower().startswith("#f")
    assert dark["base"].lower().startswith("#1")


def test_catppuccin_inherits_overrides():
    from biome_fm.views.theme import load_theme
    dark = load_theme("dark")
    mocha = load_theme("catppuccin-mocha")
    assert mocha["accent"] != dark["accent"]
    assert mocha["accent"] == "#89b4fa"


def test_theme_changed_dataclass():
    from biome_fm.event_bus import ThemeChanged
    e = ThemeChanged(name="dark", tokens={"base": "#1c1c1e"})
    assert e.name == "dark"
    assert e.tokens["base"] == "#1c1c1e"


def test_find_theme_user_dir(tmp_path, monkeypatch):
    from biome_fm.views import theme as theme_module
    from biome_fm.views.theme import load_theme
    (tmp_path / "my-custom.toml").write_text('[tokens]\nbase = "#aabbcc"\n', encoding="utf-8")
    monkeypatch.setattr(theme_module, "_user_themes_dir", lambda: tmp_path)
    tokens = load_theme("my-custom")
    assert tokens["base"] == "#aabbcc"
