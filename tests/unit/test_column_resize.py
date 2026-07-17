"""Unit tests for PaneView auto-resize on set_items."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QHeaderView

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _items(n: int) -> list[FileItem]:
    return [
        FileItem(name=f"f{i}.txt", path=Path(f"/tmp/f{i}.txt"), is_dir=False, size=0, modified=0.0)
        for i in range(n)
    ]


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    return v


def test_resize_called_on_set_items(view: PaneView) -> None:
    mock_resize = MagicMock()
    with patch.object(view._table.horizontalHeader(), "resizeSections", mock_resize):
        view.set_items(_items(10))
    mock_resize.assert_called_once_with(QHeaderView.ResizeMode.ResizeToContents)


def test_no_resize_on_large_dir(view: PaneView) -> None:
    mock_resize = MagicMock()
    with patch.object(view._table.horizontalHeader(), "resizeSections", mock_resize):
        view.set_items(_items(501))
    mock_resize.assert_not_called()
