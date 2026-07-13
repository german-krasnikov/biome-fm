"""Test search panel overlay integration."""
import pytest

from biome_fm.panel_manager import PanelManager, PanelState
from biome_fm.qt import QSplitter, Qt, QWidget
from biome_fm.views.ai_chat_panel import AIChatPanel
from biome_fm.views.panel_coordinator import PanelCoordinator
from biome_fm.views.preview_panel import PreviewPanel
from biome_fm.views.search_panel import SearchResultsPanel


@pytest.fixture
def coord(qtbot):
    mgr = PanelManager()
    left = QWidget()
    right = QWidget()
    preview = PreviewPanel()
    ai = AIChatPanel()
    search = SearchResultsPanel()
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(left)
    splitter.addWidget(right)
    splitter.addWidget(preview)
    splitter.addWidget(ai)
    splitter.addWidget(search)
    preview.hide()
    ai.hide()
    search.hide()
    parent = QWidget()
    qtbot.addWidget(parent)
    c = PanelCoordinator(
        mgr,
        {"preview": preview, "ai": ai, "search": search},
        left, right, splitter, parent,
    )
    return c, mgr, search


def test_search_overlay_shows(coord):
    c, mgr, search = coord
    c.toggle("search", "left")
    assert mgr.state("search") == PanelState.OVERLAY


def test_search_overlay_hides_preview(coord):
    c, mgr, search = coord
    c.toggle("preview", "left")
    assert mgr.state("preview") == PanelState.OVERLAY
    c.toggle("search", "left")
    assert mgr.state("preview") == PanelState.HIDDEN
    assert mgr.state("search") == PanelState.OVERLAY


def test_search_close_restores(coord):
    c, mgr, search = coord
    c.toggle("search", "left")
    c.toggle("search", "left")
    assert mgr.state("search") == PanelState.HIDDEN
