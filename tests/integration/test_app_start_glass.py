"""Integration tests for glass availability gate and window-show fallback."""
from __future__ import annotations

import importlib
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

import biome_fm.views.glass as glass
from biome_fm.views.glass import configure_glass
from biome_fm.views.glass_style import mark_glass


def test_configure_glass_without_lib_leaves_window_opaque(qtbot, monkeypatch):
    monkeypatch.setattr(glass, "_HAS_LIB", False)
    monkeypatch.setattr(glass, "_warned", False)
    window = QMainWindow()
    qtbot.addWidget(window)

    result = configure_glass(window, True)

    assert result is False
    assert window._glass_cfg is False
    assert not window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_configure_glass_with_lib_marks_window(qtbot, monkeypatch):
    monkeypatch.setattr(glass, "_HAS_LIB", True)
    window = QMainWindow()
    qtbot.addWidget(window)

    result = configure_glass(window, True)
    assert result is True
    assert window._glass_cfg is True
    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # disabled: no mark
    window2 = QMainWindow()
    qtbot.addWidget(window2)
    result2 = configure_glass(window2, False)
    assert result2 is False
    assert window2._glass_cfg is False
    assert not window2.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_window_shown_when_glass_runtime_error(qtbot, qapp, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["biome-fm"])
    # ensure module is importable (may already be in sys.modules)
    entry = importlib.import_module("biome_fm.__main__")

    monkeypatch.setattr(glass, "prepare_glass", lambda w: False)
    monkeypatch.setattr(glass, "enable_glass", lambda w: False)

    window = QMainWindow()
    qtbot.addWidget(window)
    mark_glass(window)
    window._glass_cfg = True

    try:
        entry._show(qapp, window)
    finally:
        qapp.setStyle("Fusion")

    assert window.isVisible()
    assert not window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
