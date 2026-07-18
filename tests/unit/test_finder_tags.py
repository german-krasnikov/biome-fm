"""Tests for macOS Finder tag reader."""
import sys
from pathlib import Path
from unittest.mock import patch

from biome_fm.models.finder_tags import finder_tag_color, get_finder_tags


def test_finder_tag_color_known():
    assert finder_tag_color("Red") == "#ff6b6b"


def test_finder_tag_color_unknown():
    assert finder_tag_color("Custom") is None


def test_non_darwin_returns_empty():
    if sys.platform == "darwin":
        with patch("biome_fm.models.finder_tags._getxattr", side_effect=OSError):
            assert get_finder_tags(Path("/nonexistent")) == []
    else:
        assert get_finder_tags(Path("/any")) == []


def test_darwin_parses_tags():
    if sys.platform != "darwin":
        return
    import plistlib
    tags_data = plistlib.dumps(["Red\n6", "Blue\n4"])
    with patch("biome_fm.models.finder_tags._getxattr", return_value=tags_data):
        result = get_finder_tags(Path("/test"))
    assert result == ["Red", "Blue"]


def test_darwin_oserror():
    if sys.platform != "darwin":
        return
    with patch("biome_fm.models.finder_tags._getxattr", side_effect=OSError("no attr")):
        assert get_finder_tags(Path("/test")) == []


# ── F279: set_finder_tags ─────────────────────────────────────────────────────

def test_set_finder_tags_calls_setxattr(monkeypatch):
    import biome_fm.models.finder_tags as m
    if sys.platform != "darwin":
        import pytest
        pytest.skip("macOS only")
    calls: list = []
    monkeypatch.setattr(m._libc, "setxattr", lambda *a: (calls.append(a), 0)[1])
    m.set_finder_tags(Path("/fake/file.txt"), ["Red", "Work"])
    assert calls


def test_set_finder_tags_noop_non_darwin():
    from biome_fm.models.finder_tags import set_finder_tags
    if sys.platform == "darwin":
        import pytest
        pytest.skip("non-darwin only")
    # Should be a no-op, no exception
    set_finder_tags(Path("/any"), ["Red"])
