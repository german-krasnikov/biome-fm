"""Unit tests for LeaderFilter event filter."""
import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit, QWidget

from biome_fm.presenters.leader_handler import LeaderHandler
from biome_fm.views.leader_filter import LeaderFilter
from biome_fm.views.which_key_popup import WhichKeyPopup


def _make_key(char: str) -> QKeyEvent:
    return QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_unknown, Qt.KeyboardModifier.NoModifier, char)


@pytest.fixture
def setup(qtbot):
    handler = LeaderHandler()
    popup = WhichKeyPopup()
    qtbot.addWidget(popup)
    f = LeaderFilter(handler, popup)
    w = QWidget()
    qtbot.addWidget(w)
    return handler, popup, f, w


def test_leader_filter_feeds_handler(qtbot, setup):
    handler, popup, f, w = setup
    handler.register("\\r", lambda: None)
    ev = _make_key("\\")
    consumed = f.eventFilter(w, ev)
    assert consumed is True
    assert handler._buffer == "\\"


def test_leader_filter_skips_text_widgets(qtbot, setup):
    handler, popup, f, _ = setup
    handler.register("\\r", lambda: None)
    edit = QLineEdit()
    qtbot.addWidget(edit)
    ev = _make_key("\\")
    consumed = f.eventFilter(edit, ev)
    assert consumed is False
    assert handler._buffer == ""  # not fed


def test_leader_filter_emits_action(qtbot, setup):
    handler, popup, f, w = setup
    called = []
    handler.register("\\r", lambda: called.append(1))
    signals = []
    f.action_triggered.connect(signals.append)

    f.eventFilter(w, _make_key("\\"))   # pending
    f.eventFilter(w, _make_key("r"))    # triggered

    assert called == [1]
    assert signals == ["triggered"]


def test_leader_filter_reset_on_unknown_key(qtbot, setup):
    handler, popup, f, w = setup
    handler.register("\\r", lambda: None)
    f.eventFilter(w, _make_key("\\"))   # pending → active
    consumed = f.eventFilter(w, _make_key("x"))  # reset
    # Should consume (was active) and not crash
    assert consumed is True
    assert handler._buffer == ""
