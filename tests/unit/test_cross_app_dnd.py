"""F323 — Cross-App Drag-and-Drop: accept text/uri-list from external apps."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest


class _FakeDragEvent:
    """Minimal fake drag event carrying QMimeData."""

    def __init__(self, mime):
        self._mime = mime
        self.accepted = False
        self._action = None

    def mimeData(self):
        return self._mime

    def acceptProposedAction(self):
        self.accepted = True

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.accepted = False

    def setDropAction(self, a):
        self._action = a

    def modifiers(self):
        from PySide6.QtCore import Qt
        return Qt.KeyboardModifier.NoModifier

    def proposedAction(self):
        from PySide6.QtCore import Qt
        return Qt.DropAction.CopyAction

    def pos(self):
        from PySide6.QtCore import QPoint
        return QPoint(0, 0)


@pytest.fixture
def pane(qtbot):
    from biome_fm.views.pane_view import PaneView
    v = PaneView()
    qtbot.addWidget(v)
    v.show()
    return v


def test_drag_enter_accepts_urls(pane):
    from PySide6.QtCore import QMimeData, QUrl
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("/tmp/foo.txt")])
    event = _FakeDragEvent(mime)
    pane._table.dragEnterEvent(event)
    assert event.accepted


def test_drop_accepts_urls(pane, tmp_path):
    from PySide6.QtCore import QMimeData, QUrl
    src = tmp_path / "file.txt"
    src.write_text("x")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(src))])
    event = _FakeDragEvent(mime)

    received = []
    pane.files_dropped.connect(lambda paths, move, target: received.append(paths))

    pane._table.dropEvent(event)

    assert event.accepted
    assert received
    assert Path(str(src)) in received[0]
