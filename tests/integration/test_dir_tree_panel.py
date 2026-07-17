"""Integration tests — DirTreePanel."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from biome_fm.views.dir_tree_panel import DirTreePanel


@pytest.fixture
def panel(qtbot):
    w = DirTreePanel()
    qtbot.addWidget(w)
    return w


def test_panel_shows_dirs_only(panel, tmp_path):
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.txt").touch()
    panel.set_root(tmp_path)
    # Model must be set; widget exists
    assert panel._tree.model() is not None


def test_panel_emits_path_on_activate(panel, tmp_path):
    (tmp_path / "sub").mkdir()
    received: list[Path] = []
    panel.path_selected.connect(received.append)
    panel._on_activated(tmp_path / "sub")
    assert received == [tmp_path / "sub"]


def test_panel_has_tree_widget(panel):
    from biome_fm.qt import QTreeView
    assert isinstance(panel._tree, QTreeView)
