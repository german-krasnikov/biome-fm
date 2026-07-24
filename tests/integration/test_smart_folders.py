"""Integration tests for Smart Folders sidebar wiring."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.models.search_template_store import SearchTemplate
from biome_fm.views.sidebar_panel import SidebarPanel


@pytest.fixture
def panel(qtbot):
    w = SidebarPanel()
    qtbot.addWidget(w)
    w.show()
    return w


def test_set_smart_folders_populates_children(panel):
    templates = [
        SearchTemplate("find py", "*.py", "wildcard"),
        SearchTemplate("find logs", "*.log", "wildcard"),
    ]
    panel.set_smart_folders(templates)
    section = panel._tree.topLevelItem(4)
    assert section.childCount() == 2
    assert section.child(0).text(0) == "find py"
    assert section.child(1).text(0) == "find logs"


def test_set_smart_folders_stores_template(panel):
    t = SearchTemplate("find py", "*.py", "wildcard")
    panel.set_smart_folders([t])
    section = panel._tree.topLevelItem(4)
    stored = section.child(0).data(0, 256)
    assert stored is t


def test_smart_folder_activated_signal(panel, qtbot):
    templates = [SearchTemplate("find py", "*.py", "wildcard")]
    panel.set_smart_folders(templates)

    section = panel._tree.topLevelItem(4)
    child = section.child(0)

    received = []
    panel.smart_folder_activated.connect(received.append)
    panel._tree.itemActivated.emit(child, 0)

    assert len(received) == 1
    assert received[0].name == "find py"
    assert received[0].pattern == "*.py"


def test_set_smart_folders_clears_previous(panel):
    panel.set_smart_folders([SearchTemplate("old", "*.old", "wildcard")])
    panel.set_smart_folders([SearchTemplate("new", "*.new", "wildcard")])
    section = panel._tree.topLevelItem(4)
    assert section.childCount() == 1
    assert section.child(0).text(0) == "new"
