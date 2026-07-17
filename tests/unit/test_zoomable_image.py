"""Unit tests for ZoomableImageWidget."""
import pytest

from biome_fm.views._zoomable_image import ZoomableImageWidget


@pytest.fixture
def widget(qtbot):
    w = ZoomableImageWidget()
    qtbot.addWidget(w)
    return w


def test_initial_scale_one(widget):
    assert widget._scale == 1.0


def test_zoom_in(widget):
    widget._zoom_in()
    assert widget._scale > 1.0


def test_reset_on_double_click(widget):
    widget._zoom_in()
    assert widget._scale > 1.0
    widget._reset()
    assert widget._scale == 1.0
