"""TDD: F285 — Directory Comparison Highlight."""
from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import ComparePresenter


# ── Qt-free: compare_dirs logic ──────────────────────────────────────────────

def test_compare_dirs_identifies_differences(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()

    (left / "extra.txt").write_text("only on left")
    (left / "common.txt").write_text("same content")
    (right / "common.txt").write_text("same content")
    (right / "other.txt").write_text("only on right")
    # Touch mtime to be the same for common.txt
    ts = time.time()
    os.utime(left / "common.txt", (ts, ts))
    os.utime(right / "common.txt", (ts, ts))

    result = ComparePresenter.compare_dirs(left, right)
    assert result["extra.txt"] == "left_only"
    assert result["other.txt"] == "right_only"
    assert result["common.txt"] == "same"


def test_compare_dirs_same_files(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()

    ts = time.time()
    for d in (left, right):
        (d / "a.txt").write_text("hello")
        os.utime(d / "a.txt", (ts, ts))

    result = ComparePresenter.compare_dirs(left, right)
    assert all(v == "same" for v in result.values())


def test_compare_dirs_differs_on_size_change(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()

    ts = time.time()
    (left / "f.txt").write_text("short")
    (right / "f.txt").write_text("longer content here")
    os.utime(left / "f.txt", (ts, ts))
    os.utime(right / "f.txt", (ts, ts))

    result = ComparePresenter.compare_dirs(left, right)
    assert result["f.txt"] == "differs"


# ── Qt: DirectoryModel.set_compare_result colors ─────────────────────────────

def test_directory_model_compare_colors(qtbot) -> None:
    from biome_fm.models.directory_model import DirectoryModel
    from biome_fm.qt import QColor, Qt

    model = DirectoryModel()
    items = [
        FileItem(name="left_only.txt", path=Path("/left_only.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="right_only.txt", path=Path("/right_only.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="differs.txt", path=Path("/differs.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="same.txt", path=Path("/same.txt"), is_dir=False, size=10, modified=0.0),
    ]
    model.set_items(items)
    model.set_compare_result({
        "left_only.txt": "left_only",
        "right_only.txt": "right_only",
        "differs.txt": "differs",
        "same.txt": "same",
    })

    _role = Qt.ItemDataRole.ForegroundRole

    def _color(row: int) -> QColor | None:
        brush = model.data(model.index(row, 0), _role)
        return brush.color() if brush is not None else None

    left_color = _color(0)
    right_color = _color(1)
    differs_color = _color(2)
    same_color = _color(3)

    # left_only → green-ish (high green component)
    assert left_color is not None
    assert left_color.green() > left_color.red()

    # right_only → red-ish
    assert right_color is not None
    assert right_color.red() > right_color.green()

    # differs → yellow-ish (both red and green high, blue low)
    assert differs_color is not None
    assert differs_color.red() > 100
    assert differs_color.green() > 100

    # same → default (None)
    assert same_color is None
