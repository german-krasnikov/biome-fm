"""Integration tests for apply_theme — requires Qt (offscreen)."""
import pytest


def test_apply_theme_dark(qapp):
    from biome_fm.views.theme import apply_theme
    apply_theme(qapp, "dark")
    assert "#1c1c1e" in qapp.styleSheet()


def test_apply_theme_light(qapp):
    from biome_fm.views.theme import apply_theme
    apply_theme(qapp, "light")
    assert "#f2f2f7" in qapp.styleSheet()


def test_theme_switch_fires_event(qapp):
    from biome_fm.event_bus import ThemeChanged, bus
    from biome_fm.views.theme import apply_theme
    received: list = []
    bus.subscribe(ThemeChanged, received.append)
    try:
        apply_theme(qapp, "light")
        assert len(received) == 1
        assert received[0].name == "light"
    finally:
        bus.unsubscribe(ThemeChanged, received.append)


def test_apply_palette_sets_colors(qapp):
    from PySide6.QtGui import QColor, QPalette
    from biome_fm.views.theme import apply_theme
    apply_theme(qapp, "dark")
    assert qapp.palette().color(QPalette.ColorRole.Window) == QColor("#1c1c1e")
