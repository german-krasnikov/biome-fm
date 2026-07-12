"""Tests for ForegroundRole coloring in DirectoryModel."""

from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem
from biome_fm.qt import QColor, Qt


def _make_item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=is_dir, size=0, modified=0.0)


def _color(model: DirectoryModel, row: int) -> QColor | None:
    idx = model.index(row, 0)
    result = model.data(idx, Qt.ItemDataRole.ForegroundRole)
    if result is None:
        return None
    return result.color()


@pytest.fixture
def model(qtbot):
    m = DirectoryModel()
    m.set_items([
        FileItem(name="..", path=Path("/tmp"), is_dir=True, size=0, modified=0.0),
        _make_item("script.py"),
        _make_item("archive.zip"),
        _make_item("photo.jpg"),
        _make_item("notes.txt"),
        _make_item("video.mp4"),
        _make_item("unknown.xyz"),
        _make_item("somedir", is_dir=True),
        _make_item(".gitignore"),
    ])
    return m


def test_py_file_green(model):
    # row 1 = script.py
    c = _color(model, 1)
    assert c is not None
    assert c.name().lower() == "#009e73"


def test_zip_file_red(model):
    # row 2 = archive.zip
    c = _color(model, 2)
    assert c is not None
    assert c.name().lower() == "#d55e00"


def test_jpg_purple(model):
    # row 3 = photo.jpg
    c = _color(model, 3)
    assert c is not None
    assert c.name().lower() == "#cc79a7"


def test_dir_no_color(model):
    # row 7 = somedir
    c = _color(model, 7)
    assert c is None


def test_dotdot_no_color(model):
    # row 0 = ..
    c = _color(model, 0)
    assert c is None


def test_unknown_ext_no_color(model):
    # row 6 = unknown.xyz
    c = _color(model, 6)
    assert c is None


def test_hidden_file_dim(model):
    # row 8 = .gitignore
    c = _color(model, 8)
    assert c is not None
    assert c.name().lower() == "#565f89"
