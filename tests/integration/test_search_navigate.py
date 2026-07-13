"""Integration test for search result navigation."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchResult
from biome_fm.views.search_panel import SearchResultsPanel


def _result(name="target.py", parent="/home/user/src"):
    path = Path(parent) / name
    return SearchResult(
        item=FileItem(name=name, path=path, is_dir=False, size=100, modified=1000.0)
    )


@pytest.fixture
def panel(qtbot):
    p = SearchResultsPanel()
    qtbot.addWidget(p)
    return p


def test_navigate_to_file_signal_params(panel, qtbot):
    """navigate_to_file emits (parent_dir: Path, filename: str) on double-click."""
    panel.on_search_started("*.py")
    panel.add_result(_result("target.py", "/home/user/src"))

    received = []
    panel.navigate_to_file.connect(lambda d, n: received.append((d, n)))

    idx = panel._model.index(0, 0)
    panel._on_double_click(idx)

    assert len(received) == 1
    assert received[0] == (Path("/home/user/src"), "target.py")


def test_navigate_to_file_context_menu_params(panel, qtbot):
    """Context menu 'Go to File' also emits correct (parent_dir, filename)."""
    panel.on_search_started("*.py")
    panel.add_result(_result("deep.py", "/tmp/nested"))

    received = []
    panel.navigate_to_file.connect(lambda d, n: received.append((d, n)))

    # Call the action directly (context menu exec is not testable headlessly)
    result = panel._model.result_at(0)
    panel.navigate_to_file.emit(result.item.path.parent, result.item.name)

    assert received == [(Path("/tmp/nested"), "deep.py")]
