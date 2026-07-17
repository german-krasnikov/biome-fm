"""Integration tests for AIRenameDialog."""
import pytest
from pytestqt.qtbot import QtBot

from biome_fm.views.ai_rename_dialog import AIRenameDialog


def test_dialog_shows_names(qtbot: QtBot) -> None:
    dlg = AIRenameDialog(["foo.txt", "bar.jpg"], ["baz.txt", None])
    qtbot.addWidget(dlg)
    # table should have 2 rows
    assert dlg._table.rowCount() == 2
    assert dlg._table.item(0, 0).text() == "foo.txt"
    assert dlg._table.item(1, 0).text() == "bar.jpg"


def test_no_suggestions_label(qtbot: QtBot) -> None:
    dlg = AIRenameDialog(["foo.txt", "bar.jpg"], [None, None])
    qtbot.addWidget(dlg)
    assert not dlg._label.isHidden()
    assert "No suggestions" in dlg._label.text()
