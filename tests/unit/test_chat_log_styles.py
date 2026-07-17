"""Test _make_styles returns different colors for light vs dark."""
from biome_fm.views._chat_log import _make_styles


def test_dark_user_background():
    s = _make_styles(dark=True)
    assert "background:#1a2840" in s["user"][1]


def test_light_user_background():
    s = _make_styles(dark=False)
    # Light mode: light-blue background, not the dark navy
    assert "background:#1a2840" not in s["user"][1]
    assert "background:#cce4ff" in s["user"][1]


def test_light_vs_dark_differ():
    assert _make_styles(dark=True) != _make_styles(dark=False)


def test_dark_error_background():
    s = _make_styles(dark=True)
    assert "background:#2a1a1a" in s["error"][1]


def test_light_error_background():
    s = _make_styles(dark=False)
    assert "background:#2a1a1a" not in s["error"][1]
    assert "background:#ffd6d6" in s["error"][1]
