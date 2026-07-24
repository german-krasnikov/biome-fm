"""Unit tests for Item #32 — JumpBar/ContextBar theme token compliance."""
import pathlib
from string import Template


ROOT = pathlib.Path(__file__).parent.parent.parent

BANNED = ["rgba(0,0,0", "#2a2a3a", "#444", "color: white"]


def test_no_hardcoded_colors_jump_bar():
    src = (ROOT / "src/biome_fm/views/jump_bar.py").read_text()
    for pattern in BANNED:
        assert pattern not in src, f"{pattern!r} still in jump_bar.py"


def test_no_hardcoded_colors_context_bar():
    src = (ROOT / "src/biome_fm/views/_context_bar.py").read_text()
    for pattern in BANNED:
        assert pattern not in src, f"{pattern!r} still in _context_bar.py"


def test_qss_template_has_jump_bar_selector():
    from biome_fm.views.theme import _QSS_TMPL  # type: ignore[attr-defined]
    assert "jump_bar_label" in _QSS_TMPL


def test_qss_template_has_context_chip_selector():
    from biome_fm.views.theme import _QSS_TMPL  # type: ignore[attr-defined]
    assert "context_chip" in _QSS_TMPL


def test_light_theme_substitutes_jump_bar():
    from biome_fm.views.theme import _QSS_TMPL, load_theme  # type: ignore[attr-defined]
    tokens = load_theme("light")
    qss = Template(_QSS_TMPL).substitute(tokens)
    assert "jump_bar_label" in qss
    assert "#e5e5ea" in qss   # light surface2
    assert "#1c1c1e" in qss   # light text


def test_dark_theme_substitutes_context_chip():
    from biome_fm.views.theme import _QSS_TMPL, load_theme  # type: ignore[attr-defined]
    tokens = load_theme("dark")
    qss = Template(_QSS_TMPL).substitute(tokens)
    assert "context_chip" in qss
    assert "#3a3a3c" in qss   # dark surface2
    assert "#48484a" in qss   # dark border
