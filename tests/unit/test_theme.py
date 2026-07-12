"""Unit tests for theme QSS generation — no Qt needed."""
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
