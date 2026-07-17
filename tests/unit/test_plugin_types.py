"""Unit tests for plugins/types._DARK_FALLBACK."""


def test_dark_fallback_has_required_keys():
    from biome_fm.plugins.types import _DARK_FALLBACK
    assert "base" in _DARK_FALLBACK and "accent" in _DARK_FALLBACK


def test_dark_fallback_importable_from_views_theme():
    """Backward-compat alias still works."""
    from biome_fm.views.theme import _DARK_FALLBACK
    assert "base" in _DARK_FALLBACK
