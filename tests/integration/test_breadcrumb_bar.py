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
    assert bar._stack.currentIndex() == 0


def test_show_error_activates_combo(bar):
    bar.show_error("Not found")
    assert bar._stack.currentWidget() is bar._combo
    assert "Error" in bar._combo.lineEdit().text()


def test_nav_history(bar):
    bar.set_nav_history([Path("/a"), Path("/b"), Path("/c")])
    assert bar._combo.count() == 3


def test_set_path_shows_crumb(bar):
    bar.set_path(Path("/foo/bar"))
    assert bar._stack.currentIndex() == 0


def test_active_segment_is_last(bar):
    bar.set_path(Path("/foo/bar"))
    buttons = bar.findChildren(_SegmentButton)
    active = [b for b in buttons if b.property("crumb_active")]
    assert len(active) == 1
    assert active[0].text() == "bar"


def test_vertical_wheel_does_not_horizontal_scroll(bar, qtbot):
    """Vertical wheel must not scroll breadcrumb horizontally."""
    bar.setFixedWidth(40)
    bar.set_path(Path("/a/b/c/d/e/f/g/h/i"))
    bar.show()
    qtbot.wait(50)
    sb = bar._scroll.horizontalScrollBar()
    before = sb.value()
    _send_wheel(bar._scroll, dx=30, dy=200)
    assert sb.value() == before


def test_horizontal_wheel_scrolls_right(bar, qtbot):
    """Negative dx scrolls toward the end of the path."""
    bar.setFixedWidth(40)
    bar.set_path(Path("/a/b/c/d/e/f/g/h/i/j/k"))
    bar.show()
    qtbot.wait(100)
    sb = bar._scroll.horizontalScrollBar()
    sb.setValue(0)
    _send_wheel(bar._scroll, dx=-240)
    if sb.maximum() > 0:
        assert sb.value() > 0


def test_horizontal_wheel_scrolls_left(bar, qtbot):
    """Positive dx scrolls toward the start of the path."""
    bar.setFixedWidth(40)
    bar.set_path(Path("/a/b/c/d/e/f/g/h/i/j/k"))
    bar.show()
    qtbot.wait(100)
    sb = bar._scroll.horizontalScrollBar()
    sb.setValue(sb.maximum())
    before = sb.value()
    _send_wheel(bar._scroll, dx=240)
    if sb.maximum() > 0:
        assert sb.value() < before


def test_swipe_does_not_emit_navigation(bar, qtbot):
    """Horizontal swipe must not fire back/forward navigation signals."""
    assert not hasattr(bar, 'back_requested')
    assert not hasattr(bar, 'forward_requested')


def test_bar_height_is_fixed(bar, qtbot):
    bar.set_path(Path("/a/b/c/d/e/f/g/h/i/j"))
    bar.show()
    assert bar.height() <= 40


def test_has_scroll_area(bar):
    from PySide6.QtWidgets import QScrollArea
    assert hasattr(bar, "_scroll")
    assert isinstance(bar._scroll, QScrollArea)


def test_arrows_hidden_for_short_path(bar, qtbot):
    bar.setFixedWidth(800)
    bar.set_path(Path("/foo"))
    bar.show()
    qtbot.wait(50)
    assert not bar._left_arrow.isVisible()
    assert not bar._right_arrow.isVisible()


def test_scrolled_to_end_on_long_path(bar, qtbot):
    bar.setFixedWidth(80)
    bar.set_path(Path("/a/b/c/d/e/f/g/h/i/j/k/l/m"))
    bar.show()
    qtbot.wait(200)
    sb = bar._scroll.horizontalScrollBar()
    if sb.maximum() > 0:
        assert abs(sb.value() - sb.maximum()) <= 30


def test_breadcrumb_visible_after_repeated_navigation(qtbot, tmp_path):
    """Breadcrumb must remain visible after navigating in/out of directories."""
    bar = BreadcrumbBar()
    qtbot.addWidget(bar)
    bar.show()
    qtbot.waitExposed(bar)

    child = tmp_path / "subdir"
    child.mkdir()

    for _ in range(5):
        bar.set_path(child)
        qtbot.wait(50)
        bar.set_path(tmp_path)
        qtbot.wait(50)

    assert bar._crumb.width() > 0
    assert bar._stack.currentIndex() == 0


def test_segment_drag_mime_data(bar, qtbot):
    """Dragging a breadcrumb segment produces correct MIME: uri-list + text/plain."""
    bar.set_path(Path("/foo/bar"))
    btn = next(b for b in bar.findChildren(_SegmentButton) if b.text() == "foo")
    from biome_fm.views.dnd_utils import make_path_mime
    mime = make_path_mime([str(btn._path)])
    assert mime.hasUrls()
    assert mime.hasText()
    assert mime.text() == str(Path("/foo"))
    urls = mime.urls()
    assert len(urls) == 1
    assert urls[0].toLocalFile() == str(Path("/foo"))


def test_segment_has_drag_start(bar, qtbot):
    """_SegmentButton initializes _drag_start for drag support."""
    bar.set_path(Path("/foo/bar"))
    btn = next(b for b in bar.findChildren(_SegmentButton) if b.text() == "bar")
    assert hasattr(btn, "_drag_start")
    assert btn._drag_start is None
