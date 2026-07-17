"""Unit tests for DirectoryModel cut-path visual state."""
from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem
from biome_fm.qt import QColor, Qt


@pytest.fixture()
def model(qapp):
    m = DirectoryModel()
    items = [
        FileItem(name="foo.txt", path=Path("/tmp/foo.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="bar.txt", path=Path("/tmp/bar.txt"), is_dir=False, size=20, modified=0.0),
    ]
    m.set_items(items)
    return m


def test_cut_paths_returns_dim_color(model):
    model.set_cut_paths({Path("/tmp/foo.txt")})
    idx = model.index(0, 0)
    brush = model.data(idx, Qt.ItemDataRole.ForegroundRole)
    assert brush is not None
    color = brush.color()
    # Should be gray/dimmed — alpha < 255 or gray shade
    assert color.alpha() < 255 or color.red() == color.green() == color.blue()


def test_uncut_path_not_dimmed(model):
    model.set_cut_paths({Path("/tmp/foo.txt")})
    idx = model.index(1, 0)
    # bar.txt is NOT cut — should get normal ext-based or None color, not the dim gray
    brush = model.data(idx, Qt.ItemDataRole.ForegroundRole)
    if brush is not None:
        color = brush.color()
        # Not the special dim color (alpha=100, r=g=b=128)
        assert not (color.alpha() == 100 and color.red() == 128)


def test_clear_cut_restores_normal(model):
    model.set_cut_paths({Path("/tmp/foo.txt")})
    model.set_cut_paths(set())
    idx = model.index(0, 0)
    brush = model.data(idx, Qt.ItemDataRole.ForegroundRole)
    # After clear, foo.txt should not have the dim cut color
    if brush is not None:
        color = brush.color()
        assert not (color.alpha() == 100 and color.red() == 128)
