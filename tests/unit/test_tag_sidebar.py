"""F280 — Tag sidebar section tests (requires Qt offscreen)."""
from __future__ import annotations

import pytest

from biome_fm.views.sidebar_panel import SidebarPanel


@pytest.fixture
def panel(qtbot):
    p = SidebarPanel()
    qtbot.addWidget(p)
    return p


def test_tag_section_lists_tags(panel: SidebarPanel) -> None:
    panel.set_tags([("red-tag", "#ff0000"), ("blue-tag", "#0000ff")])
    tags_item = panel._tree.topLevelItem(3)  # Tags section (index 3)
    assert tags_item is not None
    assert tags_item.text(0) == "Tags"
    assert tags_item.childCount() == 2
    assert tags_item.child(0).text(0) == "red-tag"
    assert tags_item.child(1).text(0) == "blue-tag"


def test_tag_click_emits_signal(panel: SidebarPanel, qtbot) -> None:
    panel.set_tags([("work", "#ff8800")])
    tags_item = panel._tree.topLevelItem(3)
    child = tags_item.child(0)
    with qtbot.waitSignal(panel.tag_activated, timeout=1000) as blocker:
        panel._tree.itemActivated.emit(child, 0)
    assert blocker.args[0] == "work"
