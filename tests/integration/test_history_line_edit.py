"""Unit tests for _HistoryLineEdit (needs Qt, runs offscreen)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from biome_fm.views.main_window import _HistoryLineEdit


def _press(widget: _HistoryLineEdit, key: Qt.Key) -> None:
    widget.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
    )


def test_push_deduplicates(qapp: object) -> None:
    w = _HistoryLineEdit()
    w.push("ls")
    w.push("cd /")
    w.push("ls")
    assert w._history == ["ls", "cd /"]


def test_capped_at_30(qapp: object) -> None:
    w = _HistoryLineEdit()
    for i in range(35):
        w.push(f"cmd{i}")
    assert len(w._history) == 30


def test_up_key_navigates(qapp: object) -> None:
    w = _HistoryLineEdit()
    w.push("ls")
    w.push("pwd")
    _press(w, Qt.Key.Key_Up)
    assert w.text() == "pwd"
    _press(w, Qt.Key.Key_Up)
    assert w.text() == "ls"


def test_down_key_returns_empty(qapp: object) -> None:
    w = _HistoryLineEdit()
    w.push("ls")
    _press(w, Qt.Key.Key_Up)
    _press(w, Qt.Key.Key_Down)
    assert w.text() == ""
