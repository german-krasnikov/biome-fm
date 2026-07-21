"""Integration tests for ZoomableImageWidget fit-to-window / 1:1 features."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QPixmap

from biome_fm.views._zoomable_image import ZoomableImageWidget


@pytest.fixture
def widget(qtbot):
    w = ZoomableImageWidget()
    w.resize(400, 300)
    qtbot.addWidget(w)
    w.show()
    return w


@pytest.fixture
def widget_with_image(widget):
    px = QPixmap(1000, 1000)
    px.fill()
    widget.set_pixmap(px)
    return widget


def test_fit_to_window_scales_down(widget_with_image):
    widget_with_image.fit_to_window()
    assert widget_with_image._scale < 1.0


def test_actual_size_resets_scale(widget_with_image):
    widget_with_image.fit_to_window()
    widget_with_image.actual_size()
    assert widget_with_image._scale == 1.0


def test_fit_to_window_null_pixmap_no_crash(widget):
    widget.fit_to_window()  # must not raise


def test_key_0_fits_to_window(qtbot, widget_with_image):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    QTest.keyClick(widget_with_image, Qt.Key.Key_0)
    assert widget_with_image._scale < 1.0


def test_key_1_actual_size(qtbot, widget_with_image):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    widget_with_image.fit_to_window()
    QTest.keyClick(widget_with_image, Qt.Key.Key_1)
    assert widget_with_image._scale == 1.0


def test_fit_to_window_rotated_90_swaps_dims(qtbot):
    """After 90° rotation effective dims are swapped; scale must reflect that."""
    w = ZoomableImageWidget()
    w.resize(400, 300)
    qtbot.addWidget(w)
    w.show()

    px = QPixmap(1000, 500)
    px.fill()
    w.set_pixmap(px)
    w._angle = 90  # force rotation without calling _update

    w.fit_to_window()

    # after 90° rotation effective dims swap: px 1000x500 → effective 500x1000
    vp = w.viewport().size()
    expected = min(vp.width() / 500, vp.height() / 1000)
    assert abs(w._scale - expected) < 1e-9
