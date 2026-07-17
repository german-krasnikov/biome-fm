"""Integration tests for search results context menu (file ops)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchResult
from biome_fm.qt import QApplication, QMenu, QTimer
from biome_fm.views.search_panel import SearchResultsPanel


def _result(name="foo.txt"):
    return SearchResult(
        item=FileItem(name=name, path=Path("/tmp") / name, is_dir=False, size=100, modified=1000.0)
    )


@pytest.fixture
def panel(qtbot):
    p = SearchResultsPanel()
    qtbot.addWidget(p)
    p.show()
    return p


def test_context_menu_shows_on_result(panel, qtbot):
    panel.on_search_started("test")
    panel.add_result(_result("target.py"))

    opened_menus: list[QMenu] = []

    def dismiss():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMenu) and w.isVisible():
                opened_menus.append(w)
                w.close()

    QTimer.singleShot(0, dismiss)
    pos = panel._table.visualRect(panel._model.index(0, 0)).center()
    panel._table.customContextMenuRequested.emit(pos)
    qtbot.wait(100)

    assert opened_menus, "context menu was not shown"
    actions = [a.text() for a in opened_menus[0].actions()]
    assert any("Copy" in a for a in actions)
    assert any("Move" in a for a in actions)
    assert any("Delete" in a for a in actions)
    assert any("Reveal" in a for a in actions)


def test_context_action_signal_emitted(panel, qtbot):
    """context_action_requested signal fires when Copy is triggered."""
    panel.on_search_started("test")
    r = _result("target.py")
    panel.add_result(r)

    received: list = []
    panel.context_action_requested.connect(lambda result, action: received.append((result, action)))

    # Directly invoke the internal handler to bypass menu popup
    panel._emit_context_action(r, "copy")

    assert len(received) == 1
    assert received[0][0] is r
    assert received[0][1] == "copy"
