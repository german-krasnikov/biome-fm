"""Integration tests for Undo/Redo UI signals in MainWindow."""
import pytest

from biome_fm.views.main_window import MainWindow


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    return w


def test_undo_signal_exists(win):
    assert hasattr(win, "undo_requested")


def test_redo_signal_exists(win):
    assert hasattr(win, "redo_requested")
