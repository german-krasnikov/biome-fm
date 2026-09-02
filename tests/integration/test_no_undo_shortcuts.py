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


def test_edit_menu_has_no_adjacent_separators(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    edit_action = next(
        a for a in win.menuBar().actions() if a.text().startswith("&Edit")
    )
    edit_menu = edit_action.menu()
    actions = edit_menu.actions()
    for i in range(len(actions) - 1):
        assert not (actions[i].isSeparator() and actions[i + 1].isSeparator()), (
            f"Adjacent separators at positions {i} and {i+1}"
        )
