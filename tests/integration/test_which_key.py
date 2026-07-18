"""Integration test for which-key popup (F290)."""
import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget

from biome_fm.presenters.leader_handler import LeaderHandler
from biome_fm.views.leader_filter import LeaderFilter
from biome_fm.views.which_key_popup import WhichKeyPopup


def test_popup_appears_after_leader(qtbot):
    handler = LeaderHandler()
    handler.register("\\r", lambda: None)
    popup = WhichKeyPopup()
    qtbot.addWidget(popup)
    f = LeaderFilter(handler, popup, timer_ms=100)  # short delay for test

    w = QWidget()
    qtbot.addWidget(w)
    w.show()

    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backslash, Qt.KeyboardModifier.NoModifier, "\\")
    f.eventFilter(w, ev)  # → "pending", starts timer

    qtbot.wait(200)  # wait for timer to fire

    assert popup.isVisible()


def test_popup_hides_on_action(qtbot):
    handler = LeaderHandler()
    handler.register("\\r", lambda: None)
    popup = WhichKeyPopup()
    qtbot.addWidget(popup)
    f = LeaderFilter(handler, popup, timer_ms=10)

    w = QWidget()
    qtbot.addWidget(w)
    w.show()

    def _key(char):
        return QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_unknown, Qt.KeyboardModifier.NoModifier, char)

    f.eventFilter(w, _key("\\"))
    qtbot.wait(50)
    assert popup.isVisible()

    f.eventFilter(w, _key("r"))
    assert not popup.isVisible()
