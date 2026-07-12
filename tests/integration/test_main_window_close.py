"""Integration tests for MainWindow close event and AI toggle."""
import pytest

from biome_fm.views.main_window import MainWindow


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    return w


def test_close_emits_about_to_close(win, qtbot):
    with qtbot.waitSignal(win.about_to_close, timeout=1000):
        win.close()


def test_toggle_ai_panel_emits_signal(qtbot):
    from biome_fm.views.ai_chat_panel import AIChatPanel

    panel = AIChatPanel()
    w = MainWindow(ai_panel=panel)
    qtbot.addWidget(w)
    w.show()
    with qtbot.waitSignal(w.ai_toggle_requested, timeout=1000):
        w.toggle_ai_panel()


def test_splitter_sizes_returns_list(win):
    sizes = win.splitter_sizes
    assert isinstance(sizes, list)
