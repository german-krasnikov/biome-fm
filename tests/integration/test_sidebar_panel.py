"""Integration tests for SidebarPanel."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.views.sidebar_panel import SidebarPanel


@pytest.fixture
def panel(qtbot):
    w = SidebarPanel()
    qtbot.addWidget(w)
    w.show()
    return w


def test_three_sections(panel):
    tree = panel._tree
    assert tree.topLevelItemCount() == 3
    labels = [tree.topLevelItem(i).text(0) for i in range(3)]
    assert labels == ["Volumes", "Bookmarks", "Recent"]


def test_set_volumes(panel):
    paths = [Path("/"), Path("/Volumes/USB")]
    panel.set_volumes(paths)
    vol = panel._tree.topLevelItem(0)
    assert vol.childCount() == 2
    assert vol.child(0).text(0) == "/"
    assert vol.child(1).text(0) == "USB"


def test_set_bookmarks(panel):
    nodes = [
        BookmarkNode(kind="dir", path=Path("/home/user"), name="Home"),
        BookmarkNode(kind="separator"),
        BookmarkNode(kind="dir", path=Path("/tmp"), name=""),
    ]
    panel.set_bookmarks(nodes)
    bm = panel._tree.topLevelItem(1)
    # separators skipped, only dir nodes with paths
    assert bm.childCount() == 2
    assert bm.child(0).text(0) == "Home"
    assert bm.child(1).text(0) == "tmp"


def test_set_recent(panel):
    paths = [Path("/foo/bar"), Path("/baz")]
    panel.set_recent(paths)
    rec = panel._tree.topLevelItem(2)
    assert rec.childCount() == 2
    assert rec.child(0).text(0) == "bar"
    assert rec.child(1).text(0) == "baz"


def test_path_activated_signal(panel, qtbot):
    panel.set_volumes([Path("/")])
    vol = panel._tree.topLevelItem(0)
    child = vol.child(0)
    with qtbot.waitSignal(panel.path_activated, timeout=1000) as blocker:
        panel._tree.itemActivated.emit(child, 0)
    assert blocker.args[0] == Path("/")
