"""Tests for icon_provider module."""

from biome_fm.models.icon_provider import icon_for_dir, icon_for_extension


def test_icon_for_extension_returns_qicon(qtbot):
    icon = icon_for_extension("py")
    assert not icon.isNull()


def test_icon_for_dir_returns_qicon(qtbot):
    icon = icon_for_dir()
    assert not icon.isNull()


def test_icon_cache_same_object(qtbot):
    a = icon_for_extension("txt")
    b = icon_for_extension("txt")
    assert a is b
