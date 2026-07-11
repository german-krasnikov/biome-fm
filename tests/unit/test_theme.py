"""Unit tests for theme QSS generation — no Qt needed."""
from biome_fm.views.theme import _QSS, _TOKENS


def test_all_tokens_substituted():
    qss = _QSS.substitute(_TOKENS)
    # No unresolved Template placeholders remain
    assert "$" not in qss


def test_tokyo_night_base_color_present():
    qss = _QSS.substitute(_TOKENS)
    assert _TOKENS["base"] in qss      # #1A1B26
    assert _TOKENS["accent"] in qss    # #7AA2F7


def test_key_selectors_present():
    qss = _QSS.substitute(_TOKENS)
    for selector in ("QTableView", "QLineEdit", "QPushButton", "QFrame#command-palette"):
        assert selector in qss, f"Missing selector: {selector}"
