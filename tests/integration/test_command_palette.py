"""Integration tests for CommandPalette — requires Qt (offscreen)."""
import pytest

from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.views.command_palette import CommandPalette


@pytest.fixture
def reg() -> CommandRegistry:
    r = CommandRegistry()
    r.register(CommandEntry("Copy Files", "F5", lambda: None))
    r.register(CommandEntry("Move Files", "F6", lambda: None))
    r.register(CommandEntry("Delete",     "F8", lambda: None))
    return r


def test_open_shows_all_entries(qtbot, reg):
    pal = CommandPalette(reg)
    qtbot.addWidget(pal)
    pal.open()
    assert pal.isVisible()
    assert pal._list.count() == 3


def test_filter_narrows_list(qtbot, reg):
    pal = CommandPalette(reg)
    qtbot.addWidget(pal)
    pal.open()
    pal._input.setText("files")
    assert pal._list.count() == 2


def test_filter_empty_restores_all(qtbot, reg):
    pal = CommandPalette(reg)
    qtbot.addWidget(pal)
    pal.open()
    pal._input.setText("delete")
    assert pal._list.count() == 1
    pal._input.clear()
    assert pal._list.count() == 3


def test_execute_calls_callback_and_hides(qtbot, reg):
    called = []
    r = CommandRegistry()
    r.register(CommandEntry("Run", "", lambda: called.append(1)))
    pal = CommandPalette(r)
    qtbot.addWidget(pal)
    pal.open()
    pal._execute()
    assert called == [1]
    assert not pal.isVisible()


def test_escape_hides_palette(qtbot, reg):
    from PySide6.QtCore import Qt
    pal = CommandPalette(reg)
    qtbot.addWidget(pal)
    pal.open()
    qtbot.keyPress(pal._input, Qt.Key.Key_Escape)
    assert not pal.isVisible()


def test_arrow_down_moves_selection(qtbot, reg):
    from PySide6.QtCore import Qt
    pal = CommandPalette(reg)
    qtbot.addWidget(pal)
    pal.open()
    assert pal._list.currentRow() == 0
    qtbot.keyPress(pal._input, Qt.Key.Key_Down)
    assert pal._list.currentRow() == 1
