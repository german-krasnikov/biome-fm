"""F417 — Two-finger trackpad swipe back/forward (macOS NativeGesture)."""
import sys

import pytest

from PySide6.QtCore import QEvent

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS gesture only")


@pytest.fixture
def pane(qtbot, tmp_path):
    from biome_fm.views.pane_view import PaneView
    w = PaneView()
    qtbot.addWidget(w)
    w.show()
    return w


def test_event_handles_native_gesture_type_without_crash(pane):
    """The event() method must not raise on NativeGesture type events."""
    table = pane._table
    # Construct a plain QEvent with NativeGesture type — no QNativeGestureEvent
    # (which can't be instantiated in offscreen mode).
    # This verifies the dispatch guard runs without error.
    ev = QEvent(QEvent.Type.NativeGesture)
    try:
        table.event(ev)
    except Exception as exc:
        pytest.fail(f"event() raised on NativeGesture: {exc}")


def test_back_signal_on_swipe_left(pane, qtbot):
    """Negative delta.x() on SwipeNativeGesture emits back_requested."""
    try:
        from PySide6.QtCore import Qt, QPointF
        from PySide6.QtGui import QNativeGestureEvent, QPointingDevice
    except ImportError:
        pytest.skip("QNativeGestureEvent not available")

    try:
        dev = QPointingDevice.primaryPointingDevice()
        ev = QNativeGestureEvent(
            Qt.NativeGestureType.SwipeNativeGesture,
            dev,
            2,                    # fingerCount
            QPointF(0, 0),        # localPos
            QPointF(0, 0),        # scenePos
            QPointF(0, 0),        # globalPos
            -1.0,                 # value
            QPointF(-1.0, 0.0),   # delta
        )
    except Exception:
        pytest.skip("QNativeGestureEvent constructor not available in offscreen mode")

    with qtbot.waitSignal(pane.back_requested, timeout=500):
        pane._table.event(ev)


def test_forward_signal_on_swipe_right(pane, qtbot):
    """Positive delta.x() on SwipeNativeGesture emits forward_requested."""
    try:
        from PySide6.QtCore import Qt, QPointF
        from PySide6.QtGui import QNativeGestureEvent, QPointingDevice
    except ImportError:
        pytest.skip("QNativeGestureEvent not available")

    try:
        dev = QPointingDevice.primaryPointingDevice()
        ev = QNativeGestureEvent(
            Qt.NativeGestureType.SwipeNativeGesture,
            dev,
            2,                   # fingerCount
            QPointF(0, 0),       # localPos
            QPointF(0, 0),       # scenePos
            QPointF(0, 0),       # globalPos
            1.0,                 # value
            QPointF(1.0, 0.0),   # delta
        )
    except Exception:
        pytest.skip("QNativeGestureEvent constructor not available in offscreen mode")

    with qtbot.waitSignal(pane.forward_requested, timeout=500):
        pane._table.event(ev)
