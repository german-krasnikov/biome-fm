"""Integration tests for BreadcrumbBar."""
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QWheelEvent

from biome_fm.qt import Qt
from biome_fm.views.breadcrumb_bar import BreadcrumbBar, _SegmentButton


def _send_wheel(widget, dx, dy=0):
    ev = QWheelEvent(
        QPointF(10, 10), widget.mapToGlobal(QPoint(10, 10)),
        QPoint(0, 0), QPoint(dx, dy),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase, False,
    )
    widget.wheelEvent(ev)


@pytest.fixture
def bar(qtbot):
    b = BreadcrumbBar()
    qtbot.addWidget(b)
    b.show()
    return b


def test_set_path_creates_segments(bar):
    bar.set_path(Path("/foo/bar"))
    buttons = bar.findChildren(_SegmentButton)
    labels = [b.text() for b in buttons]
    assert "foo" in labels and "bar" in labels


def test_segment_click_emits_navigation(bar, qtbot):
    bar.set_path(Path("/foo/bar"))
    foo_btn = next(b for b in bar.findChildren(_SegmentButton) if b.text() == "foo")
    with qtbot.waitSignal(bar.path_entered, timeout=1000) as sig:
        qtbot.mouseClick(foo_btn, Qt.MouseButton.LeftButton)
    assert sig.args[0] == str(Path("/foo"))


def test_edit_mode_on_activate_edit(bar):
    bar.set_path(Path("/foo"))
    bar.activate_edit()
    assert bar._stack.currentWidget() is bar._combo


def test_enter_commits_edit(bar, qtbot):
    bar.activate_edit()
    bar._combo.lineEdit().setText("/tmp/test")
    with qtbot.waitSignal(bar.path_entered, timeout=1000) as sig:
        qtbot.keyClick(bar._combo.lineEdit(), Qt.Key.Key_Return)
    assert sig.args[0] == "/tmp/test"
    assert bar._stack.currentWidget() is bar._crumb


def test_show_error_activates_combo(bar):
    bar.show_error("Not found")
    assert bar._stack.currentWidget() is bar._combo
    assert "Error" in bar._combo.lineEdit().text()


def test_nav_history(bar):
    bar.set_nav_history([Path("/a"), Path("/b"), Path("/c")])
    assert bar._combo.count() == 3


def test_set_path_shows_crumb(bar):
    bar.set_path(Path("/foo/bar"))
    assert bar._stack.currentWidget() is bar._crumb


def test_active_segment_is_last(bar):
    bar.set_path(Path("/foo/bar"))
    buttons = bar.findChildren(_SegmentButton)
    active = [b for b in buttons if b.property("crumb_active")]
    assert len(active) == 1
    assert active[0].text() == "bar"


def test_swipe_left_emits_back(bar, qtbot):
    with qtbot.waitSignal(bar.back_requested, timeout=1000):
        _send_wheel(bar._crumb, dx=-120)


def test_swipe_right_emits_forward(bar, qtbot):
    with qtbot.waitSignal(bar.forward_requested, timeout=1000):
        _send_wheel(bar._crumb, dx=120)


def test_sub_threshold_no_emit(bar):
    signals = []
    bar.back_requested.connect(lambda: signals.append(1))
    _send_wheel(bar._crumb, dx=-60)
    assert signals == []


def test_accumulates_to_threshold(bar):
    signals = []
    bar.back_requested.connect(lambda: signals.append(1))
    _send_wheel(bar._crumb, dx=-60)
    _send_wheel(bar._crumb, dx=-60)
    assert signals == [1]


def test_vertical_scroll_ignored(bar):
    signals = []
    bar.back_requested.connect(lambda: signals.append(1))
    _send_wheel(bar._crumb, dx=30, dy=200)
    assert signals == []
