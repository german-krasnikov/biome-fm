"""F405 — Mouse back/forward button integration test."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from biome_fm.views.pane_view import PaneView


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    v.show()
    return v


def _mouse_event(btn: Qt.MouseButton) -> QMouseEvent:
    return QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(0, 0),
        QPointF(0, 0),
        btn,
        btn,
        Qt.KeyboardModifier.NoModifier,
    )


def test_back_button_emits_back_requested(qtbot, view):
    with qtbot.waitSignal(view.back_requested, timeout=500):
        view._table.mousePressEvent(_mouse_event(Qt.MouseButton.BackButton))


def test_forward_button_emits_forward_requested(qtbot, view):
    with qtbot.waitSignal(view.forward_requested, timeout=500):
        view._table.mousePressEvent(_mouse_event(Qt.MouseButton.ForwardButton))
