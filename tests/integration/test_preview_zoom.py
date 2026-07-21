"""F430 — Ctrl+Wheel text zoom in PreviewPanel."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from biome_fm.views.preview_panel import PreviewPanel


@pytest.fixture
def panel(qtbot):
    w = PreviewPanel()
    qtbot.addWidget(w)
    w.show()
    return w


def _wheel(ctrl: bool, up: bool) -> QWheelEvent:
    delta = 120 if up else -120
    mod = Qt.KeyboardModifier.ControlModifier if ctrl else Qt.KeyboardModifier.NoModifier
    return QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        mod,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )


def _font_size(panel: PreviewPanel) -> int:
    return panel._text_view.document().defaultFont().pointSize()


def test_ctrl_wheel_up_zooms_in(panel):
    before = _font_size(panel)
    panel.eventFilter(panel._text_view, _wheel(ctrl=True, up=True))
    assert _font_size(panel) > before


def test_ctrl_wheel_down_zooms_out(panel):
    before = _font_size(panel)
    panel.eventFilter(panel._text_view, _wheel(ctrl=True, up=False))
    assert _font_size(panel) < before


def test_plain_wheel_does_not_zoom(panel):
    before = _font_size(panel)
    panel.eventFilter(panel._text_view, _wheel(ctrl=False, up=True))
    assert _font_size(panel) == before
