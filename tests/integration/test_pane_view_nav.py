"""Integration tests for PaneView nav bar, sorting, DnD, context menu."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QTimer
from PySide6.QtGui import QContextMenuEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QMenu, QPushButton

from biome_fm.views.pane_side_view import PaneSideView
from biome_fm.views.pane_view import _MIME, PaneView


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    v.show()
    return v


# ── Nav signals ─────────────────────────────────────────────────────────────

def _nav_btn(view: PaneView, name: str) -> QPushButton:
    return next(b for b in view.findChildren(QPushButton) if b.objectName() == name)


def test_nav_back_signal(qtbot, view):
    with qtbot.waitSignal(view.back_requested, timeout=500):
        _nav_btn(view, "nav_back").click()


def test_nav_forward_signal(qtbot, view):
    with qtbot.waitSignal(view.forward_requested, timeout=500):
        _nav_btn(view, "nav_forward").click()


def test_nav_up_signal(qtbot, view):
    with qtbot.waitSignal(view.up_requested, timeout=500):
        _nav_btn(view, "nav_up").click()


# ── Sorting ─────────────────────────────────────────────────────────────────

def test_sorting_enabled(view):
    assert view._table.isSortingEnabled()


# ── DnD ─────────────────────────────────────────────────────────────────────

def test_files_dropped_signal(qtbot, view):
    received: list[tuple] = []
    view.files_dropped.connect(lambda paths, move, folder: received.append((paths, move)))

    mime = QMimeData()
    mime.setData(_MIME, b"/tmp/foo.txt\n/tmp/bar.txt")
    event = QDropEvent(
        QPointF(5.0, 5.0),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    view._table.dropEvent(event)

    assert len(received) == 1
    paths, move = received[0]
    assert Path("/tmp/foo.txt") in paths
    assert Path("/tmp/bar.txt") in paths
    assert move is False


def test_files_dropped_move_action(qtbot, view):
    """Shift held during drop → move=True (Shift-move detection)."""
    received: list[tuple] = []
    view.files_dropped.connect(lambda paths, move, folder: received.append((paths, move)))

    mime = QMimeData()
    mime.setData(_MIME, b"/tmp/x.txt")
    event = QDropEvent(
        QPointF(5.0, 5.0),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier,
    )
    view._table.dropEvent(event)

    assert received[0][1] is True


# ── Context menu ─────────────────────────────────────────────────────────────

def test_context_menu_signal_emits(view):
    """context_action_requested signal emits correctly."""
    received: list[str] = []
    view.context_action_requested.connect(received.append)
    view.context_action_requested.emit("copy")
    assert received == ["copy"]


def test_context_menu_all_actions(qtbot, view):
    """contextMenuEvent creates menu with copy/move/delete/rename actions."""
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

    assert "Copy" in captured
    assert "Move" in captured
    assert "Delete" in captured
    assert "Rename" in captured


# ── PaneSideView.set_active ──────────────────────────────────────────────────

@pytest.fixture
def side_view(qtbot):
    w = PaneSideView()
    qtbot.addWidget(w)
    w.show()
    return w


def test_set_active_true(side_view):
    side_view.set_active(True)
    assert side_view.property("active") is True


def test_set_active_false(side_view):
    side_view.set_active(True)
    side_view.set_active(False)
    assert side_view.property("active") is False
