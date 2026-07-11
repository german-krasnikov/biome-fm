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


def test_cmd_line_hidden_by_default(win):
    assert not win._cmd_line.isVisible()
