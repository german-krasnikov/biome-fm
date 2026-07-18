"""Unit tests for WhichKeyPopup."""
import pytest
from PySide6.QtWidgets import QLabel
from biome_fm.views.which_key_popup import WhichKeyPopup


def test_show_hints_displays(qtbot):
    popup = WhichKeyPopup()
    qtbot.addWidget(popup)
    popup.show_hints([("r", "\\r"), ("h", "\\h")], None)
    assert popup.isVisible()
    assert "r" in popup._label.text()


def test_hide_popup(qtbot):
    popup = WhichKeyPopup()
    qtbot.addWidget(popup)
    popup.show_hints([("r", "\\r")], None)
    popup.hide_popup()
    assert not popup.isVisible()


def test_show_hints_empty_hides(qtbot):
    popup = WhichKeyPopup()
    qtbot.addWidget(popup)
    popup.show()
    popup.show_hints([], None)
    assert not popup.isVisible()
