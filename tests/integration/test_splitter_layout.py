"""Integration tests for splitter layout — stretch factors, collapsible, breadcrumb minimum size."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.qt import QWidget
from biome_fm.views.breadcrumb_bar import _CrumbRow, _CrumbScrollArea
from biome_fm.views.main_window import MainWindow


@pytest.fixture()
def window(qtbot):
    left = QWidget()
    right = QWidget()
    preview = QWidget()
    ai = QWidget()
    w = MainWindow(left=left, right=right, preview_panel=preview, ai_panel=ai)
    qtbot.addWidget(w)
    return w


def test_splitter_has_at_least_two_panes(window):
    sp = window.splitter
    assert sp.count() >= 2


def test_splitter_collapsible_false(window):
    sp = window.splitter
    assert sp.isCollapsible(0) is False
    assert sp.isCollapsible(1) is False


def test_set_pane_ratio_50_50(window, qtbot):
    sp = window.splitter
    sp.setSizes([600, 600, 0, 0])
    window._set_pane_ratio(0.5)
    sizes = sp.sizes()
    assert sizes[0] == sizes[1]


def test_set_pane_ratio_25_75(window, qtbot):
    sp = window.splitter
    sp.setSizes([600, 600, 0, 0])
    window._set_pane_ratio(0.25)
    sizes = sp.sizes()
    total = sizes[0] + sizes[1]
    assert abs(sizes[0] - int(total * 0.25)) <= 1


def test_set_pane_ratio_75_25(window, qtbot):
    sp = window.splitter
    sp.setSizes([600, 600, 0, 0])
    window._set_pane_ratio(0.75)
    sizes = sp.sizes()
    total = sizes[0] + sizes[1]
    assert abs(sizes[0] - int(total * 0.75)) <= 1


def test_breadcrumb_minimum_size_small(qtbot):
    from pathlib import Path
    row = _CrumbRow()
    scroll = _CrumbScrollArea(row)  # takes ownership of row
    qtbot.addWidget(scroll)
    row.set_path(Path("/very/long/path/with/many/segments/that/keeps/going"))
    hint = scroll.minimumSizeHint()
    assert hint.width() <= 100
    row.setParent(None)  # prevent double-delete
