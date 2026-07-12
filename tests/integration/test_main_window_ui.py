"""Integration tests for main_window UI polish."""
import pytest

from biome_fm.views.main_window import MainWindow


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    w.show()
    return w


def test_splitter_fills_height(win, qtbot):
    win.resize(1200, 800)
    qtbot.waitExposed(win)
    splitter_h = win._splitter.height()
    action_bar_h = win.action_bar.height()
    assert splitter_h > action_bar_h * 3


def test_has_menubar_menus(win):
    mb = win.menuBar()
    titles = [mb.actions()[i].text() for i in range(mb.actions().__len__())]
    assert "&File" in titles
    assert "&Edit" in titles
    assert "&Navigate" in titles
    assert "&View" in titles


def test_nav_signals_exist(win):
    for sig_name in ("back_requested", "forward_requested", "up_requested", "home_requested"):
        assert hasattr(win, sig_name)


def test_cmd_line_visible_by_default(win):
    assert win._cmd_line.isVisible()


def test_ai_button_in_toolbar(win):
    assert hasattr(win, "_act_ai")
    assert win._act_ai.isCheckable()


def test_cmd_submitted_signal(qtbot, win):
    received = []
    win.command_submitted.connect(received.append)
    win._cmd_line.setText("ls")
    win._cmd_line.returnPressed.emit()
    assert received == ["ls"]
    assert win._cmd_line.text() == ""


def test_cmd_empty_not_submitted(qtbot, win):
    received = []
    win.command_submitted.connect(received.append)
    win._cmd_line.setText("   ")
    win._cmd_line.returnPressed.emit()
    assert received == []
