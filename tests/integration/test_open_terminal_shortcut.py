"""Integration test: Open Terminal Here in pane context menu."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QPoint, QTimer
from PySide6.QtGui import QContextMenuEvent

from biome_fm.qt import QApplication, QMenu


@pytest.fixture
def view(qtbot):
    from biome_fm.views.pane_view import PaneView
    w = PaneView()
    qtbot.addWidget(w)
    w.show()
    return w


def test_context_menu_has_open_terminal(view, qtbot):
    """Right-click context menu must include 'Open Terminal Here'."""
    captured: list[str] = []

    def grab_and_close():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMenu) and w.isVisible():
                captured.extend(a.text().split("\t")[0] for a in w.actions())
                w.close()
                return

    QTimer.singleShot(0, grab_and_close)
    pos = view._table.rect().center()
    event = QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, pos, view._table.mapToGlobal(pos)
    )
    view._table.contextMenuEvent(event)

    assert any("Terminal" in t for t in captured), (
        f"'Open Terminal Here' not found in: {captured}"
    )
