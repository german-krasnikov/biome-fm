"""TDD: SearchResultsPanel emits preview_requested on selection."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchResult
from biome_fm.views.search_panel import SearchResultsPanel


def _result(name="foo.txt", is_dir=False):
    return SearchResult(
        item=FileItem(name=name, path=Path("/tmp") / name, is_dir=is_dir, size=100, modified=1000.0)
    )


@pytest.fixture()
def panel(qtbot):
    p = SearchResultsPanel()
    qtbot.addWidget(p)
    p.show()
    return p


def test_search_panel_emits_preview_signal_on_selection(panel, qtbot):
    panel.add_result(_result("readme.txt"))
    with qtbot.waitSignal(panel.preview_requested, timeout=1000) as blocker:
        panel._table.selectRow(0)
    assert blocker.args[0] is not None
    assert blocker.args[0].name == "readme.txt"


def test_search_preview_updates_on_row_change(panel, qtbot):
    panel.add_result(_result("a.txt"))
    panel.add_result(_result("b.txt"))
    panel._table.selectRow(0)
    with qtbot.waitSignal(panel.preview_requested, timeout=1000) as blocker:
        panel._table.selectRow(1)
    assert blocker.args[0].name == "b.txt"


def test_search_preview_clears_on_clear(panel, qtbot):
    panel.add_result(_result("readme.txt"))
    panel._table.selectRow(0)
    with qtbot.waitSignal(panel.preview_requested, timeout=1000) as blocker:
        panel.clear()
    assert blocker.args[0] is None


def test_search_preview_clears_on_directory(panel, qtbot):
    panel.add_result(_result("mydir", is_dir=True))
    signals = []
    panel.preview_requested.connect(lambda item: signals.append(item))
    panel._table.selectRow(0)
    qtbot.wait(100)
    assert signals == [None]
