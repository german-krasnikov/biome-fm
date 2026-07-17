"""Unit tests for undo/redo QAction label updates in MainWindow."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from biome_fm.views.main_window import MainWindow


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    return w


def test_undo_label_shows_description(win):
    win.update_undo_redo_labels(undo_desc="Copy", redo_desc=None)
    assert "Copy" in win._act_undo.text()


def test_redo_label_shows_description(win):
    win.update_undo_redo_labels(undo_desc=None, redo_desc="Move")
    assert "Move" in win._act_redo.text()


def test_empty_stack_default_label(win):
    win.update_undo_redo_labels(undo_desc=None, redo_desc=None)
    assert win._act_undo.text().startswith("&Undo")
    assert win._act_redo.text().startswith("&Redo")
