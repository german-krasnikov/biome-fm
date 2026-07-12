"""Integration tests for PaneView table layout."""
import pytest
from biome_fm.models.directory_model import COL_EXT, COL_MODIFIED, COL_NAME, COL_SIZE
from biome_fm.qt import QHeaderView
from biome_fm.views.pane_view import PaneView


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    return v


def test_vertical_header_hidden(view):
    assert not view._table.verticalHeader().isVisible()


def test_alternating_row_colors(view):
    assert view._table.alternatingRowColors()


def test_grid_hidden(view):
    assert not view._table.showGrid()


def test_uniform_row_heights(view):
    assert view._table.uniformRowHeights()


def test_row_height_fixed(view):
    vh = view._table.verticalHeader()
    assert vh.defaultSectionSize() == 22
    assert vh.sectionResizeMode(0) == QHeaderView.ResizeMode.Fixed


def test_name_column_stretch(view):
    hh = view._table.horizontalHeader()
    assert hh.sectionResizeMode(COL_NAME) == QHeaderView.ResizeMode.Stretch


def test_other_columns_interactive(view):
    hh = view._table.horizontalHeader()
    for col in (COL_SIZE, COL_MODIFIED, COL_EXT):
        assert hh.sectionResizeMode(col) == QHeaderView.ResizeMode.Interactive
