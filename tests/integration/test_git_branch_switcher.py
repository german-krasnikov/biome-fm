"""Integration test: MainWindow._git_btn emits branch_clicked on click."""
from biome_fm.qt import Qt


def test_branch_clicked_signal(qtbot):
    from biome_fm.views.main_window import MainWindow

    win = MainWindow(None, None)
    qtbot.addWidget(win)
    win.update_git_branch("main")
    received = []
    win.branch_clicked.connect(lambda: received.append(True))
    qtbot.mouseClick(win._git_btn, Qt.MouseButton.LeftButton)
    assert received
