"""Guard: no undo/redo QActions or signals on MainWindow."""
from PySide6.QtGui import QAction

from biome_fm.views.main_window import MainWindow


def test_no_undo_redo_qactions(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    action_texts = [a.text() for a in win.findChildren(QAction)]
    assert not any("Undo" in t for t in action_texts)
    assert not any("Redo" in t for t in action_texts)


def test_no_undo_redo_signals(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    assert not hasattr(win, "undo_requested")
    assert not hasattr(win, "redo_requested")
    assert not hasattr(win, "update_undo_redo_labels")
