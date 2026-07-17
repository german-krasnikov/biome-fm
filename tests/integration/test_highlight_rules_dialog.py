"""Integration tests for HighlightRulesDialog."""
import pytest
from biome_fm.views.highlight_rules_dialog import HighlightRulesDialog


@pytest.fixture
def dialog(qtbot):
    dlg = HighlightRulesDialog([{"pattern": "*.log", "color": "#888888"}])
    qtbot.addWidget(dlg)
    return dlg


def test_dialog_shows_rules(dialog):
    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 0).text() == "*.log"


def test_add_remove_buttons(dialog, qtbot):
    initial = dialog._table.rowCount()
    dialog._btn_add.click()
    assert dialog._table.rowCount() == initial + 1
    dialog._table.selectRow(0)
    dialog._btn_remove.click()
    assert dialog._table.rowCount() == initial
