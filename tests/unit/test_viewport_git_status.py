"""F329 — Viewport-only git status enrichment."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem


def _items(n: int = 10) -> list[FileItem]:
    return [
        FileItem(name=f"f{i}.py", path=Path(f"/repo/f{i}.py"), is_dir=False, size=0, modified=0.0)
        for i in range(n)
    ]


def test_set_git_status_stores_full_dict(qtbot):
    model = DirectoryModel()
    model.set_items(_items(5))
    statuses = {Path(f"/repo/f{i}.py"): " M" for i in range(5)}
    model.set_git_status(statuses, frozenset())
    assert model._git_statuses == statuses


def test_data_changed_emitted_for_visible_range_only(qtbot):
    model = DirectoryModel()
    model.set_items(_items(10))
    statuses = {Path(f"/repo/f{i}.py"): " M" for i in range(10)}

    emitted_ranges: list[tuple[int, int]] = []

    def _capture(tl, br, roles):
        emitted_ranges.append((tl.row(), br.row()))

    model.dataChanged.connect(_capture)
    model.set_git_status(statuses, frozenset(), visible_range=(2, 5))

    assert emitted_ranges == [(2, 5)]
