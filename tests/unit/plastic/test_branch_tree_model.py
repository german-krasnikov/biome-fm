"""Unit tests for BranchTreeModel and _DetailsPanel.show_branch."""
from __future__ import annotations

from datetime import datetime

import pytest

from biome_fm.plastic._models import Branch

_D = datetime(2024, 1, 1)


def _br(name: str, parent: str = "") -> Branch:
    return Branch(name=name, date=_D, owner="x", parent=parent)


# ── BranchTreeModel ───────────────────────────────────────────────────────────

def test_branch_tree_groups_by_prefix(qtbot):
    from biome_fm.plastic._components import BranchTreeModel
    m = BranchTreeModel()
    m.reset([_br("/main/task"), _br("/main"), _br("/dev/fix")])
    root = m.model.invisibleRootItem()
    group_texts = [root.child(i).text() for i in range(root.rowCount())]
    # /main is root-prefixed — goes in "(root)"; /main/task goes in "/main"; /dev/fix in "/dev"
    assert "(root)" in group_texts
    assert "/main" in group_texts
    assert "/dev" in group_texts


def test_branch_tree_current_bold(qtbot):
    from biome_fm.plastic._components import BranchTreeModel
    m = BranchTreeModel()
    m.reset([_br("/main"), _br("/dev")])
    m.set_current("/main")
    root = m.model.invisibleRootItem()
    found = False
    for gi in range(root.rowCount()):
        group = root.child(gi)
        for bi in range(group.rowCount()):
            leaf = group.child(bi)
            br = leaf.data(BranchTreeModel.UserRole)
            if br is not None and br.name == "/main":
                assert leaf.font().bold()
                found = True
    assert found, "leaf for /main not found"


def test_branch_at_returns_none_for_group(qtbot):
    from biome_fm.plastic._components import BranchTreeModel
    m = BranchTreeModel()
    m.reset([_br("/main/task")])
    group_idx = m.model.index(0, 0)  # group item, no UserRole
    assert m.branch_at(group_idx) is None


def test_branch_at_returns_branch_for_leaf(qtbot):
    from biome_fm.plastic._components import BranchTreeModel
    m = BranchTreeModel()
    br = _br("/main/task")
    m.reset([br])
    root = m.model.invisibleRootItem()
    group = root.child(0)
    leaf_idx = m.model.indexFromItem(group.child(0))
    assert m.branch_at(leaf_idx) is br


def test_branch_tree_leaf_displays_short_name(qtbot):
    from biome_fm.plastic._components import BranchTreeModel
    m = BranchTreeModel()
    m.reset([_br("/main/task")])
    root = m.model.invisibleRootItem()
    # find the /main group and its leaf
    for gi in range(root.rowCount()):
        g = root.child(gi)
        if g.text() == "/main":
            assert g.child(0).text() == "task"
            return
    pytest.fail("group /main not found")


# ── _DetailsPanel.show_branch ─────────────────────────────────────────────────

def test_show_branch_with_parent(qtbot):
    from biome_fm.plastic._components import _DetailsPanel
    panel = _DetailsPanel()
    qtbot.addWidget(panel)
    br = Branch(name="/main/task", date=_D, owner="alice", parent="/main")
    panel.show_branch(br)
    text = panel._body.toPlainText()
    assert "Parent" in text
    assert "/main" in text


def test_show_branch_no_parent(qtbot):
    from biome_fm.plastic._components import _DetailsPanel
    panel = _DetailsPanel()
    qtbot.addWidget(panel)
    br = Branch(name="/main", date=_D, owner="alice")
    panel.show_branch(br)
    assert "Parent" not in panel._body.toPlainText()
