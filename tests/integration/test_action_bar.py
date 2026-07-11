"""Integration tests for ActionBar widget."""
import pytest

from biome_fm.qt import QPushButton
from biome_fm.views.action_bar import ActionBar


@pytest.fixture
def bar(qtbot):
    w = ActionBar()
    qtbot.addWidget(w)
    return w


def test_action_bar_has_8_buttons(bar):
    assert len(bar.findChildren(QPushButton)) == 8


def test_copy_button_emits_signal(bar, qtbot):
    btn = next(b for b in bar.findChildren(QPushButton) if "Copy" in b.text())
    with qtbot.waitSignal(bar.copy_requested, timeout=1000):
        btn.click()


def test_delete_button_emits_signal(bar, qtbot):
    btn = next(b for b in bar.findChildren(QPushButton) if "Delete" in b.text())
    with qtbot.waitSignal(bar.delete_requested, timeout=1000):
        btn.click()
