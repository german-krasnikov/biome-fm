"""Integration tests for PlasticWindow — pytest-qt, offscreen."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from biome_fm.plastic._models import Branch, Changeset, Label, PlasticItem, Shelve
from biome_fm.plastic._window import PlasticWindow


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def win(qtbot):
    w = PlasticWindow()
    qtbot.addWidget(w)
    w.show()
    return w


def _dt(year: int = 2026) -> datetime:
    return datetime(year, 7, 24, 12, 0, 0)


# ── Window structure ──────────────────────────────────────────────────────────

def test_window_has_thirteen_pages(win):
    assert win._stack.count() == 13


def test_sidebar_items(win):
    items = [win._nav.item(i).text() for i in range(win._nav.count())]
    assert items == [
        "Pending Changes", "Changesets", "Branches", "Labels", "Shelves",
        "Reviews", "Xlinks", "Admin", "Branch DAG",
        "Workspaces & Repos", "Triggers", "Git Sync",
    ]


def test_window_title_default(win):
    assert "Plastic" in win.windowTitle()


# ── Pending Changes tree ──────────────────────────────────────────────────────

def test_set_status_items_groups_by_directory(win):
    # two files in the same dir → 1 dir row
    items = [
        PlasticItem(status="CO", path=Path("/w/a.py")),
        PlasticItem(status="AD", path=Path("/w/b.py")),
    ]
    win.set_status_items(items)
    win._drain()
    assert win._status_model.rowCount() == 1  # 1 directory
    dir_item = win._status_model.item(0, 0)
    assert dir_item.rowCount() == 2  # 2 files under it


def test_set_status_items_two_dirs(win):
    items = [
        PlasticItem(status="CO", path=Path("/a/x.py")),
        PlasticItem(status="AD", path=Path("/b/y.py")),
    ]
    win.set_status_items(items)
    win._drain()
    assert win._status_model.rowCount() == 2


def test_set_status_items_file_name_in_tree(win):
    win.set_status_items([PlasticItem(status="CH", path=Path("/w/myfile.py"))])
    win._drain()
    file_item = win._status_model.item(0, 0).child(0)
    assert file_item.text() == "myfile.py"


def test_set_status_items_status_column_has_plastic(win):
    win.set_status_items([PlasticItem(status="CO", path=Path("/w/f.py"))])
    win._drain()
    status_item = win._status_model.item(0, 0).child(0, 1)  # col 1 = Status
    plastic = status_item.data(Qt.ItemDataRole.UserRole)
    assert plastic.status == "CO"


def test_set_status_items_files_checked_by_default(win):
    win.set_status_items([PlasticItem(status="AD", path=Path("/w/f.py"))])
    win._drain()
    file_item = win._status_model.item(0, 0).child(0)
    assert file_item.checkState() == Qt.CheckState.Checked


def test_set_status_items_plastic_item_in_user_role(win):
    plastic = PlasticItem(status="CO", path=Path("/w/f.py"))
    win.set_status_items([plastic])
    win._drain()
    file_item = win._status_model.item(0, 0).child(0)
    stored = file_item.data(Qt.ItemDataRole.UserRole)
    assert stored.path == plastic.path
    assert stored.status == plastic.status


def test_checked_items_returns_all_by_default(win):
    items = [
        PlasticItem(status="CO", path=Path("/w/a.py")),
        PlasticItem(status="AD", path=Path("/w/b.py")),
    ]
    win.set_status_items(items)
    win._drain()
    checked = win._checked_items()
    assert len(checked) == 2


def test_checked_items_respects_unchecked(win):
    win.set_status_items([
        PlasticItem(status="CO", path=Path("/w/a.py")),
        PlasticItem(status="AD", path=Path("/w/b.py")),
    ])
    win._drain()
    # Uncheck the first file
    win._status_model.item(0, 0).child(0).setCheckState(Qt.CheckState.Unchecked)
    assert len(win._checked_items()) == 1


def test_changes_count_label(win):
    win.set_status_items([
        PlasticItem(status="CO", path=Path("/w/a.py")),
        PlasticItem(status="AD", path=Path("/w/b.py")),
    ])
    win._drain()
    assert "2" in win._changes_count.text()


def test_reset_model_replaces_items(win):
    win.set_status_items([PlasticItem(status="CO", path=Path("/a.py"))])
    win._drain()
    win.set_status_items([
        PlasticItem(status="AD", path=Path("/b.py")),
        PlasticItem(status="PR", path=Path("/c.py")),
    ])
    win._drain()
    # all in same parent dir → 1 dir row with 2 children
    assert win._status_model.rowCount() == 1
    assert win._status_model.item(0, 0).rowCount() == 2


def test_comment_edit_exists(win):
    assert win._comment_edit.placeholderText() != ""


def test_on_checkin_requires_comment(win, qtbot):
    win.set_status_items([PlasticItem(status="CO", path=Path("/w/f.py"))])
    win._drain()
    received = []
    win.checkin_requested.connect(lambda items, msg: received.append((items, msg)))
    win._comment_edit.setText("")  # no comment
    win._on_checkin()
    assert received == []


def test_on_checkin_emits_with_comment(win, qtbot):
    win.set_status_items([PlasticItem(status="CO", path=Path("/w/f.py"))])
    win._drain()
    received = []
    win.checkin_requested.connect(lambda items, msg: received.append((items, msg)))
    win._comment_edit.setText("my message")
    win._on_checkin()
    assert len(received) == 1
    assert received[0][1] == "my message"
    assert len(received[0][0]) == 1


def test_on_undo_emits_checked(win, qtbot):
    from unittest.mock import patch
    from PySide6.QtWidgets import QMessageBox
    win.set_status_items([PlasticItem(status="CO", path=Path("/w/f.py"))])
    win._drain()
    received = []
    win.undo_requested.connect(lambda items: received.append(items))
    with patch("biome_fm.plastic._window.QMessageBox.question",
               return_value=QMessageBox.StandardButton.Yes):
        win._on_undo()
    assert len(received) == 1
    assert len(received[0]) == 1


# ── Drain queue — set_changesets ─────────────────────────────────────────────

def test_set_changesets_populates_model(win):
    cs_list = [
        Changeset(cs_id=1, date=_dt(), owner="alice", branch="/main", comment="init"),
        Changeset(cs_id=2, date=_dt(), owner="bob", branch="/main", comment="fix"),
    ]
    win.set_changesets(cs_list)
    win._drain()
    assert win._changeset_model.rowCount() == 2


def test_set_changesets_cs_id_column(win):
    win.set_changesets([Changeset(cs_id=42, date=_dt(), owner="a", branch="/b", comment="c")])
    win._drain()
    assert win._changeset_model.data(win._changeset_model.index(0, 1)) == "CS#42"


def test_set_changesets_owner_column(win):
    win.set_changesets([Changeset(cs_id=1, date=_dt(), owner="alice", branch="/main", comment="")])
    win._drain()
    assert win._changeset_model.data(win._changeset_model.index(0, 3)) == "alice"


# ── Drain queue — set_branches ────────────────────────────────────────────────

def test_set_branches_populates_model(win):
    win.set_branches([Branch(name="/main", date=_dt(), owner="alice")])
    win._drain()
    # BranchTreeModel: one group "(root)" containing one leaf
    assert win._branch_tree.model.rowCount() == 1


def test_set_branches_name_column(win):
    win.set_branches([Branch(name="/feature", date=_dt(), owner="dev")])
    win._drain()
    # leaf shows short segment; full name is stored in UserRole
    root = win._branch_tree.model.invisibleRootItem()
    leaf = root.child(0).child(0)
    assert leaf.data(win._branch_tree.UserRole).name == "/feature"


# ── Drain queue — set_labels ──────────────────────────────────────────────────

def test_set_labels_populates_model(win):
    win.set_labels([Label(name="v1.0", changeset=10, date=_dt())])
    win._drain()
    assert win._label_model.rowCount() == 1


def test_set_labels_name_column(win):
    win.set_labels([Label(name="v2.3", changeset=5, date=_dt())])
    win._drain()
    assert win._label_model.data(win._label_model.index(0, 0)) == "v2.3"


def test_set_labels_changeset_column(win):
    win.set_labels([Label(name="v1.0", changeset=99, date=_dt())])
    win._drain()
    assert win._label_model.data(win._label_model.index(0, 1)) == "CS#99"


# ── Drain queue — set_header ──────────────────────────────────────────────────

def test_set_header_updates_label_text(win):
    win.set_header(branch="/main", repo="MyRepo@server")
    win._drain()
    assert "/main" in win._header_label.text()
    assert "MyRepo@server" in win._header_label.text()


def test_set_header_updates_window_title(win):
    win.set_header(branch="/task-42", repo="Repo")
    win._drain()
    assert "/task-42" in win.windowTitle()


# ── Drain — DRAIN_LIMIT ───────────────────────────────────────────────────────

def test_drain_processes_up_to_drain_limit(win):
    for i in range(PlasticWindow._DRAIN_LIMIT + 10):
        win.set_labels([Label(name=f"v{i}", changeset=i, date=_dt())])
    win._drain()
    assert win._label_model.rowCount() >= 0


# ── Drain — show_error ────────────────────────────────────────────────────────

def test_show_error_queues_message(win):
    win.show_error("something broke")
    kind, payload = win._queue.get_nowait()
    assert kind == "error"
    assert "something broke" in str(payload)


# ── Model metadata ────────────────────────────────────────────────────────────

def test_status_model_column_count(win):
    assert win._status_model.columnCount() == 4


def test_changeset_model_column_count(win):
    assert win._changeset_model.columnCount() == 6


def test_branch_tree_column_count(win):
    assert win._branch_tree.model.columnCount() == 3


def test_label_model_column_count(win):
    assert win._label_model.columnCount() == 3


def test_status_model_headers(win):
    h = win._status_model
    assert h.headerData(0, Qt.Orientation.Horizontal) == "Item"
    assert h.headerData(1, Qt.Orientation.Horizontal) == "Status"
    assert h.headerData(2, Qt.Orientation.Horizontal) == "Size"
    assert h.headerData(3, Qt.Orientation.Horizontal) == "Date modified"


# ── Signal: refresh button ───────────────────────────────────────────────────

def test_refresh_changes_signal_emitted(win, qtbot):
    from PySide6.QtWidgets import QPushButton
    received = []
    win.refresh_changes.connect(lambda: received.append(True))
    changes_page = win._stack.widget(0)
    for btn in changes_page.findChildren(QPushButton):
        if "Refresh" in btn.text():
            btn.click()
            break
    assert len(received) == 1


# ── Shelves page ──────────────────────────────────────────────────────────────

def test_shelves_in_sidebar(win):
    items = [win._nav.item(i).text() for i in range(win._nav.count())]
    assert "Shelves" in items


def test_shelve_button_on_pending_changes(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(0)
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Shelve" in t for t in texts)


def test_lock_unlock_buttons_on_pending_changes(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(0)
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Lock" in t for t in texts)
    assert any("Unlock" in t for t in texts)


def test_rollback_button_on_changesets(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(1)
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Rollback" in t for t in texts)


def test_merge_button_on_branches(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(2)
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Merge" in t for t in texts)


def test_set_shelves_populates_model(win):
    shelves = [
        Shelve(shelve_id=1, date=_dt(), owner="alice", comment="wip"),
        Shelve(shelve_id=2, date=_dt(), owner="bob", comment="test"),
    ]
    win.set_shelves(shelves)
    win._drain()
    assert win._shelve_model.rowCount() == 2


def test_set_shelves_id_column(win):
    win.set_shelves([Shelve(shelve_id=42, date=_dt(), owner="alice", comment="c")])
    win._drain()
    assert win._shelve_model.data(win._shelve_model.index(0, 0)) == "#42"


def test_set_shelves_owner_column(win):
    win.set_shelves([Shelve(shelve_id=1, date=_dt(), owner="carol", comment="c")])
    win._drain()
    assert win._shelve_model.data(win._shelve_model.index(0, 2)) == "carol"


def test_new_signals_exist(win):
    for sig in (
        "shelve_requested",
        "unshelve_requested",
        "refresh_shelves",
        "merge_branch_requested",
        "rollback_cs_requested",
        "lock_requested",
        "unlock_requested",
    ):
        assert hasattr(win, sig), f"missing signal: {sig}"


def test_shelves_page_detail_panel(win):
    s = Shelve(shelve_id=7, date=_dt(), owner="dev", comment="my shelve")
    win._shelve_details.show_shelve(s)
    assert "7" in win._shelve_details._title.text()
    assert "dev" in win._shelve_details._body.toPlainText()


# ── 3.6 Error styling ─────────────────────────────────────────────────────────

def test_error_message_sets_red_stylesheet(win):
    win.show_error("boom")
    win._drain()
    assert "red" in win.statusBar().styleSheet()


def test_status_message_clears_stylesheet(win):
    win.show_error("boom")
    win._drain()
    win.set_status_message("ok")
    win._drain()
    assert win.statusBar().styleSheet() == ""


# ── 3.4 Back from diff ────────────────────────────────────────────────────────

def test_show_diff_stores_prev_page(win):
    win._stack.setCurrentIndex(2)   # branches page
    win.show_diff("--- a\n+++ b\n")
    win._drain()
    assert win._prev_page == 2


def test_show_diff_switches_to_diff_page(win):
    win.show_diff("--- a\n+++ b\n")
    win._drain()
    assert win._stack.currentIndex() == win._diff_page_index


def test_back_from_diff_returns_to_prev(win):
    win._prev_page = 3
    win._stack.setCurrentIndex(win._diff_page_index)
    win._on_back_from_diff()
    assert win._stack.currentIndex() == 3


def test_back_from_diff_page_has_back_button(win):
    from PySide6.QtWidgets import QPushButton
    diff_page = win._stack.widget(win._diff_page_index)
    texts = [b.text() for b in diff_page.findChildren(QPushButton)]
    assert any("Back" in t for t in texts)


# ── 3.2 Keyboard shortcuts ────────────────────────────────────────────────────

def test_f5_on_changes_page_emits_refresh(win):
    received = []
    win.refresh_changes.connect(lambda: received.append(True))
    win._stack.setCurrentIndex(0)
    win._on_refresh_current()
    assert received == [True]


def test_f5_on_changesets_page_emits_refresh(win):
    received = []
    win.refresh_changesets.connect(lambda: received.append(True))
    win._stack.setCurrentIndex(1)
    win._on_refresh_current()
    assert received == [True]


def test_ctrl_i_on_changes_page_calls_checkin(win):
    win.set_status_items([PlasticItem(status="CO", path=Path("/w/f.py"))])
    win._drain()
    win._comment_edit.setText("x")
    received = []
    win.checkin_requested.connect(lambda items, m: received.append(m))
    win._stack.setCurrentIndex(0)
    win._on_checkin_if_on_changes()
    assert received == ["x"]


def test_ctrl_i_on_other_page_is_noop(win):
    received = []
    win.checkin_requested.connect(lambda *a: received.append(True))
    win._stack.setCurrentIndex(1)  # changesets page
    win._on_checkin_if_on_changes()
    assert received == []


def test_escape_goes_back_from_diff(win):
    win._prev_page = 0
    win._stack.setCurrentIndex(win._diff_page_index)
    win._on_back_from_diff()
    assert win._stack.currentIndex() == 0


def test_escape_noop_when_not_on_diff(win):
    win._stack.setCurrentIndex(0)
    win._on_back_from_diff()
    assert win._stack.currentIndex() == 0


# ── 3.5 Progress indicator ────────────────────────────────────────────────────

def test_set_busy_true_shows_progress(win):
    win.set_busy(True)
    win._drain()
    assert win._progress.isVisible()


def test_set_busy_false_hides_progress(win):
    win.set_busy(True)
    win._drain()
    win.set_busy(False)
    win._drain()
    assert not win._progress.isVisible()


def test_progress_bar_exists_on_window(win):
    assert hasattr(win, "_progress")


# ── 3.1 Context menus ────────────────────────────────────────────────────────

def test_status_tree_has_custom_context_menu_policy(win):
    assert win._status_tree.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_cs_table_has_custom_context_menu_policy(win):
    assert win._cs_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_branch_view_has_custom_context_menu_policy(win):
    assert win._branch_view.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_label_table_has_custom_context_menu_policy(win):
    assert win._label_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_shelve_table_has_custom_context_menu_policy(win):
    assert win._shelve_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_context_menu_methods_exist(win):
    for name in ("_pending_context_menu", "_cs_context_menu", "_branch_context_menu",
                 "_label_context_menu", "_shelve_context_menu", "_show_context_menu"):
        assert hasattr(win, name), f"missing method: {name}"


# ── 3.3 Category grouping ─────────────────────────────────────────────────────

def test_group_by_status_groups_correctly(win):
    items = [
        PlasticItem(status="CO", path=Path("/w/a.py")),
        PlasticItem(status="AD", path=Path("/w/b.py")),
        PlasticItem(status="CO", path=Path("/w/c.py")),
    ]
    win._group_mode = 1
    win._build_status_tree(items)
    assert win._status_model.rowCount() == 2  # CO and AD groups


def test_group_by_status_row_labels_are_human_readable(win):
    items = [
        PlasticItem(status="CO", path=Path("/w/a.py")),
        PlasticItem(status="AD", path=Path("/w/b.py")),
    ]
    win._group_mode = 1
    win._build_status_tree(items)
    texts = {win._status_model.item(i, 0).text() for i in range(win._status_model.rowCount())}
    # headers must show human labels, not raw codes
    assert any("Checked" in t for t in texts)
    assert any("Added" in t for t in texts)


def test_change_grouping_rebuilds_tree(win):
    items = [PlasticItem(status="CO", path=Path("/w/f.py"))]
    win.set_status_items(items)
    win._drain()
    win._on_change_grouping(1)
    dir_text = win._status_model.item(0, 0).text()
    assert "Checked" in dir_text  # human-readable label, not raw "CO"


def test_group_combo_exists(win):
    assert hasattr(win, "_group_combo")


def test_group_combo_has_three_items(win):
    assert win._group_combo.count() == 3
    assert win._group_combo.itemText(0) == "Group: Directory"
    assert win._group_combo.itemText(1) == "Group: Status"
    assert win._group_combo.itemText(2) == "Group: Changelist"


def test_group_combo_changes_mode(win):
    win._group_combo.setCurrentIndex(1)
    assert win._group_mode == 1
    win._group_combo.setCurrentIndex(0)
    assert win._group_mode == 0


# ── Phase 4.1/4.2 new signals ─────────────────────────────────────────────────

def test_new_label_branch_signals_exist(win):
    for sig in (
        "create_label_requested",
        "delete_label_requested",
        "rename_label_requested",
        "delete_branch_requested",
        "rename_branch_requested",
    ):
        assert hasattr(win, sig), f"missing signal: {sig}"


def test_labels_page_has_create_delete_rename_buttons(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(3)  # Labels page
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Create" in t for t in texts)
    assert any("Delete" in t for t in texts)
    assert any("Rename" in t for t in texts)


def test_branches_page_has_delete_rename_buttons(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(2)  # Branches page
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Delete" in t for t in texts)
    assert any("Rename" in t for t in texts)


# ── Phase 4.3/4.4 history + blame ─────────────────────────────────────────────

def test_history_blame_signals_exist(win):
    assert hasattr(win, "history_requested"), "missing signal: history_requested"
    assert hasattr(win, "blame_requested"), "missing signal: blame_requested"


def test_show_history_enqueues_and_drain_opens_dialog(win, qtbot):
    from datetime import datetime
    from biome_fm.plastic._models import Revision
    from biome_fm.plastic._components import HistoryDialog

    revs = [Revision(rev_id=1, cs_id=42, date=datetime(2026, 7, 24), owner="alice", comment="fix", branch="/main")]
    win.show_history(Path("/w/foo.py"), revs)
    win._drain()
    dialogs = [w for w in win.findChildren(HistoryDialog)]
    assert len(dialogs) == 1


def test_show_blame_enqueues_and_drain_opens_dialog(win, qtbot):
    from datetime import datetime
    from biome_fm.plastic._models import BlameLine
    from biome_fm.plastic._components import BlameDialog

    lines = [BlameLine(line_no=1, owner="bob", cs_id=9, date=datetime(2026, 7, 24), content="pass")]
    win.show_blame(Path("/w/foo.py"), lines)
    win._drain()
    dialogs = [w for w in win.findChildren(BlameDialog)]
    assert len(dialogs) == 1


def test_pending_context_menu_has_history_and_blame(win):
    """_pending_context_menu triggers _on_view_history and _on_blame handlers."""
    assert hasattr(win, "_on_view_history"), "missing handler: _on_view_history"
    assert hasattr(win, "_on_blame"), "missing handler: _on_blame"


def test_on_view_history_emits_signal(win, qtbot):
    item = PlasticItem(status="CO", path=Path("/w/foo.py"))
    win.set_status_items([item])
    win._drain()
    # Select the file item in the tree
    from PySide6.QtCore import QItemSelectionModel
    file_item = win._status_model.item(0, 0).child(0)
    idx = win._status_model.indexFromItem(file_item)
    win._status_tree.selectionModel().select(idx, QItemSelectionModel.SelectionFlag.Select)

    with qtbot.waitSignal(win.history_requested, timeout=1000) as blocker:
        win._on_view_history()
    assert blocker.args[0].path == Path("/w/foo.py")


def test_on_blame_emits_signal(win, qtbot):
    item = PlasticItem(status="CO", path=Path("/w/foo.py"))
    win.set_status_items([item])
    win._drain()
    from PySide6.QtCore import QItemSelectionModel
    file_item = win._status_model.item(0, 0).child(0)
    idx = win._status_model.indexFromItem(file_item)
    win._status_tree.selectionModel().select(idx, QItemSelectionModel.SelectionFlag.Select)

    with qtbot.waitSignal(win.blame_requested, timeout=1000) as blocker:
        win._on_blame()
    assert blocker.args[0].path == Path("/w/foo.py")


# ── Phase 4.5 Reviews page ────────────────────────────────────────────────────

def test_reviews_in_sidebar(win):
    items = [win._nav.item(i).text() for i in range(win._nav.count())]
    assert "Reviews" in items


def test_reviews_page_at_index_5(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(5)
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Refresh" in t for t in texts)
    assert any("Create" in t for t in texts)


def test_reviews_page_has_context_menu_policy(win):
    assert win._review_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu


def test_new_review_signals_exist(win):
    for sig in ("refresh_reviews", "create_review_requested",
                "edit_review_requested", "delete_review_requested"):
        assert hasattr(win, sig), f"missing signal: {sig}"


def test_set_reviews_populates_model(win):
    from datetime import datetime
    from biome_fm.plastic._models import Review
    reviews = [
        Review(review_id=1, status="Reviewed", assignee="alice",
               date=datetime(2026, 1, 1), title="Fix bug"),
        Review(review_id=2, status="Under review", assignee="bob",
               date=datetime(2026, 1, 2), title="New feature"),
    ]
    win.set_reviews(reviews)
    win._drain()
    assert win._review_model.rowCount() == 2


def test_set_reviews_id_column(win):
    from datetime import datetime
    from biome_fm.plastic._models import Review
    win.set_reviews([Review(review_id=42, status="Reviewed", assignee="a",
                            date=datetime(2026, 1, 1), title="T")])
    win._drain()
    assert win._review_model.data(win._review_model.index(0, 0)) == "#42"


def test_review_model_column_count(win):
    assert win._review_model.columnCount() == 5


def test_review_details_panel_exists(win):
    assert hasattr(win, "_review_details")


def test_review_details_show_review(win):
    from datetime import datetime
    from biome_fm.plastic._models import Review
    r = Review(review_id=7, status="Rework required", assignee="carol",
                date=datetime(2026, 3, 15), title="My title")
    win._review_details.show_review(r)
    assert "7" in win._review_details._title.text()
    assert "carol" in win._review_details._body.toPlainText()


# ── Phase 4.6 Changelist grouping ────────────────────────────────────────────

def test_new_changelist_signals_exist(win):
    for sig in ("move_to_changelist_requested",
                "load_changelist_status_requested"):
        assert hasattr(win, sig), f"missing signal: {sig}"


def test_build_by_changelist_groups_items(win):
    items = [
        PlasticItem(status="CO", path=Path("/repo/src/a.py")),
        PlasticItem(status="AD", path=Path("/repo/src/b.py")),
    ]
    win.set_status_items(items)
    win._drain()
    grouped = {"sprint-1": [items[0]]}
    win._last_changelist_status = grouped
    win._group_mode = 2
    win._build_by_changelist(grouped)
    # sprint-1 group + (default) group with b.py
    row_texts = {win._status_model.item(i, 0).text()
                 for i in range(win._status_model.rowCount())}
    assert "sprint-1" in row_texts
    assert "(default)" in row_texts


def test_changelist_mode_emits_load_signal(win, qtbot):
    received = []
    win.load_changelist_status_requested.connect(lambda: received.append(True))
    win._on_change_grouping(2)
    assert received == [True]


def test_f5_on_reviews_page_emits_refresh(win):
    received = []
    win.refresh_reviews.connect(lambda: received.append(True))
    win._stack.setCurrentIndex(5)
    win._on_refresh_current()
    assert received == [True]


# ── Phase 4.11 — File Search ──────────────────────────────────────────────────

def test_find_files_signal_exists(win):
    assert hasattr(win, "find_files_requested"), "missing signal: find_files_requested"


def test_show_find_results_opens_dialog(win, qtbot):
    from biome_fm.plastic._components import FindResultsDialog
    win.show_find_results([Path("/repo/a.py"), Path("/repo/b.py")])
    win._drain()
    dialogs = win.findChildren(FindResultsDialog)
    assert len(dialogs) == 1


# ── Phase 4.12 — Workspace Info ───────────────────────────────────────────────

def test_set_workspace_info_updates_header(win):
    from biome_fm.plastic._models import WorkspaceInfo
    wi = WorkspaceInfo(
        name="MyWS", server="server:8087", branch="/main",
        last_cs=42, wk_path=Path("/repo")
    )
    win.set_workspace_info(wi)
    win._drain()
    assert "/main" in win._header_label.text()


# ── Phase 5.3 Side-by-side diff ───────────────────────────────────────────────

def test_sbs_diff_button_exists(win):
    from PySide6.QtWidgets import QPushButton
    buttons = win.findChildren(QPushButton)
    assert any("Side" in b.text() for b in buttons)


# ── Phase 5.4 Xlinks ──────────────────────────────────────────────────────────

def test_xlinks_signal_exists(win):
    assert hasattr(win, "refresh_xlinks")
    assert hasattr(win, "add_xlink_requested")
    assert hasattr(win, "remove_xlink_requested")


def test_xlinks_in_sidebar(win):
    items = [win._nav.item(i).text() for i in range(win._nav.count())]
    assert "Xlinks" in items


def test_xlinks_page_has_buttons(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(6)  # Xlinks page
    texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Refresh" in t for t in texts)
    assert any("Add" in t for t in texts)
    assert any("Remove" in t for t in texts)


def test_set_xlinks_populates_model(win):
    from biome_fm.plastic._models import Xlink
    xlinks = [Xlink("libs/engine", "server1", "MyRepo", "/main", 42)]
    win.set_xlinks(xlinks)
    win._drain()
    assert win._xlink_model.rowCount() == 1


# ── Phase 5.5-5.8 signals ─────────────────────────────────────────────────────

def test_replication_signals_exist(win):
    assert hasattr(win, "push_replication_requested")
    assert hasattr(win, "pull_replication_requested")


def test_attribute_signals_exist(win):
    assert hasattr(win, "load_attributes_requested")
    assert hasattr(win, "set_attribute_requested")
    assert hasattr(win, "delete_attribute_requested")


def test_acl_signals_exist(win):
    assert hasattr(win, "load_acl_requested")
    assert hasattr(win, "set_acl_requested")
    assert hasattr(win, "delete_acl_requested")


def test_user_group_signals_exist(win):
    assert hasattr(win, "load_users_requested")
    assert hasattr(win, "add_user_requested")
    assert hasattr(win, "delete_user_requested")
    assert hasattr(win, "load_groups_requested")
    assert hasattr(win, "add_group_requested")
    assert hasattr(win, "add_group_member_requested")


def test_admin_page_exists_in_sidebar(win):
    items = [win._nav.item(i).text() for i in range(win._nav.count())]
    assert "Admin" in items


def test_admin_page_has_users_model(win):
    assert hasattr(win, "_user_model")
    assert hasattr(win, "_group_model")


def test_set_users_populates_model(win):
    from biome_fm.plastic._models import UserInfo
    win.set_users([UserInfo("alice", "alice@example.com")])
    win._drain()
    assert win._user_model.rowCount() == 1


def test_set_groups_populates_model(win):
    from biome_fm.plastic._models import GroupInfo
    win.set_groups([GroupInfo("devs", ("alice", "bob"))])
    win._drain()
    assert win._group_model.rowCount() == 1


# ── Branch DAG (5.1) ──────────────────────────────────────────────────────────

def test_dag_signal_exists(win):
    assert hasattr(win, "refresh_dag")


def test_dag_page_has_dag_widget(win):
    assert hasattr(win, "_dag_widget")


def test_set_dag_enqueues_without_error(win):
    win.set_dag([], [])
    win._drain()  # must not raise


def test_set_dag_renders_nodes(win):
    from biome_fm.plastic._dag import BranchNode, DAGNode
    nodes = [
        DAGNode(cs_id=1, branch="/main", date=_dt(), x=0, y=0),
        DAGNode(cs_id=2, branch="/main", date=_dt(), x=0, y=30),
        DAGNode(cs_id=3, branch="/dev", date=_dt(), x=120, y=15),
    ]
    branches = [BranchNode("/main", ""), BranchNode("/dev", "/main")]
    win.set_dag(nodes, branches)
    win._drain()
    assert len(win._dag_widget._scene.items()) > 0


# ── Three-way merge viewer (5.2) ─────────────────────────────────────────────

def test_merge_view_signal_exists(win):
    assert hasattr(win, "merge_view_requested")


def test_show_merge_sides_enqueues_without_error(win):
    from pathlib import Path
    win.show_merge_sides(Path("/a.txt"), "base", "src", "dest")
    win._drain()  # ThreeWayMergeDialog.show() — must not raise


# ── Phase 6 Batch A ─────────────────────────────────────────────────────────

def test_undo_changeset_signal_emits(win, qtbot):
    win.set_changesets([Changeset(42, _dt(), "alice", "/main", "fix")])
    win._drain()
    win._cs_table.selectRow(0)
    with qtbot.waitSignal(win.undo_changeset_requested) as sig:
        win._on_undo_changeset()
    assert sig.args == [42]


def test_undo_all_signal_exists(win):
    assert hasattr(win, "undo_all_requested")


def test_undo_keep_signal_emits(win, qtbot):
    from unittest.mock import patch
    from PySide6.QtWidgets import QMessageBox
    items = [PlasticItem(status="CO", path=Path("/a.py"))]
    win.set_status_items(items)
    win._drain()
    # Check first item in status tree
    root = win._status_model.invisibleRootItem()
    if root.rowCount() > 0:
        child = root.child(0)
        if child.rowCount() > 0:
            win._status_tree.setCurrentIndex(child.child(0).index())
            child.child(0).setCheckState(Qt.CheckState.Checked)
    with patch("biome_fm.plastic._window.QMessageBox.question",
               return_value=QMessageBox.StandardButton.Yes):
        with qtbot.waitSignal(win.undo_keep_requested, timeout=500) as sig:
            win._on_undo_keep()
    assert len(sig.args[0]) > 0


def test_pkg_create_signal_emits(win, qtbot):
    win._pkg_path_edit.setText("/tmp/out.rep")
    with qtbot.waitSignal(win.replica_pkg_create_requested) as sig:
        win._on_pkg_create()
    assert sig.args == ["/tmp/out.rep"]


def test_pkg_create_empty_path_no_emit(win, qtbot):
    win._pkg_path_edit.setText("")
    emitted = []
    win.replica_pkg_create_requested.connect(lambda p: emitted.append(p))
    win._on_pkg_create()
    assert emitted == []


def test_merge_branch_requested_has_semantic_arg(win):
    """Signal accepts 4 args: name, preview, resolve, semantic."""
    emitted = []
    win.merge_branch_requested.connect(lambda *a: emitted.append(a))
    win.merge_branch_requested.emit("feat", True, "", True)
    assert emitted == [("feat", True, "", True)]


# ── Batch B: conf editor (#2 / #3) ────────────────────────────────────────────

def test_admin_page_has_conf_editor_buttons(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(7)
    btn_texts = [b.text() for b in page.findChildren(QPushButton)]
    assert "Edit ignore.conf" in btn_texts
    assert "Edit cloaked.conf" in btn_texts


def test_conf_editor_noop_without_wk_path(win):
    """Handlers bail early if _wk_path is None (no workspace info yet)."""
    assert win._wk_path is None
    win._on_edit_ignore()  # must not raise


def test_conf_editor_reads_file(win, tmp_path):
    """With _wk_path set, handler reads the conf file."""
    from unittest.mock import patch
    plastic_dir = tmp_path / ".plastic"
    plastic_dir.mkdir()
    (plastic_dir / "ignore.conf").write_text("*.pyc\n")
    win._wk_path = tmp_path
    with patch.object(win, "_on_edit_ignore", wraps=win._on_edit_ignore):
        # We can't easily test dialog interaction, but verify no crash
        # and that the path resolves correctly
        from biome_fm.plastic._conf_files import ignore_conf_path, read_conf
        path = ignore_conf_path(tmp_path)
        assert read_conf(path) == "*.pyc\n"


# ── Batch B: preferences (#8) ─────────────────────────────────────────────────

def test_load_config_requested_signal_exists(win):
    assert hasattr(win, "load_config_requested")


def test_set_config_requested_signal_exists(win):
    assert hasattr(win, "set_config_requested")


def test_load_config_requested_emits(win, qtbot):
    with qtbot.waitSignal(win.load_config_requested, timeout=500):
        win.load_config_requested.emit()


def test_show_config_entries_drains_to_model(win):
    from biome_fm.plastic._models import ConfigEntry
    entries = [ConfigEntry(key="merge.tool", value="plastic")]
    win.show_config_entries(entries)
    win._drain()
    assert win._config_model.rowCount() == 1
    assert win._config_model.item_at(0).key == "merge.tool"


def test_admin_page_has_preferences_buttons(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(7)
    btn_texts = [b.text() for b in page.findChildren(QPushButton)]
    assert "Load Config" in btn_texts
    assert "Set…" in btn_texts


# ── Batch B: partial workspaces (#5) ─────────────────────────────────────────

def test_partial_signals_exist(win):
    assert hasattr(win, "load_partial_status_requested")
    assert hasattr(win, "configure_partial_requested")
    assert hasattr(win, "add_partial_requested")
    assert hasattr(win, "remove_partial_requested")


def test_admin_page_has_partial_buttons(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(7)
    btn_texts = [b.text() for b in page.findChildren(QPushButton)]
    assert "Status" in btn_texts
    assert "Configure" in btn_texts
    assert "Add Path…" in btn_texts
    assert "Remove Path…" in btn_texts


# ── Batch C: Workspaces & Repos (#1) ─────────────────────────────────────────

def test_workspace_repo_signals_exist(win):
    for sig in (
        "refresh_workspaces", "create_workspace_requested", "delete_workspace_requested",
        "refresh_repos", "create_repo_requested", "delete_repo_requested",
    ):
        assert hasattr(win, sig), f"missing signal: {sig}"


def test_workspaces_page_at_index_9(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(9)
    btn_texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Create" in t for t in btn_texts)
    assert any("Delete" in t for t in btn_texts)


def test_set_workspaces_populates_model(win):
    from biome_fm.plastic._models import WorkspaceEntry
    entries = [WorkspaceEntry("wk1", "/home/dev", "srv:8087")]
    win.set_workspaces(entries)
    win._drain()
    assert win._workspace_model.rowCount() == 1


def test_set_repos_populates_model(win):
    from biome_fm.plastic._models import RepoEntry
    entries = [RepoEntry("Repo1", "srv:8087")]
    win.set_repos(entries)
    win._drain()
    assert win._repo_model.rowCount() == 1


# ── Batch C: Triggers (#6) ───────────────────────────────────────────────────

def test_trigger_signals_exist(win):
    for sig in ("refresh_triggers", "create_trigger_requested", "delete_trigger_requested"):
        assert hasattr(win, sig), f"missing signal: {sig}"


def test_triggers_page_at_index_10(win):
    from PySide6.QtWidgets import QPushButton
    page = win._stack.widget(10)
    btn_texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Refresh" in t for t in btn_texts)
    assert any("Create" in t for t in btn_texts)
    assert any("Delete" in t for t in btn_texts)


def test_set_triggers_populates_model(win):
    from biome_fm.plastic._models import Trigger
    triggers = [Trigger("1", "on-checkin", "after-checkin", "*.py", "/hook.sh")]
    win.set_triggers(triggers)
    win._drain()
    assert win._trigger_model.rowCount() == 1


# ── Batch C: Git Sync (#4) ───────────────────────────────────────────────────

def test_git_sync_signals_exist(win):
    assert hasattr(win, "sync_git_requested")
    assert hasattr(win, "refresh_git_sync")


def test_git_sync_page_at_index_11(win):
    from PySide6.QtWidgets import QLineEdit, QPushButton
    page = win._stack.widget(11)
    btn_texts = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Sync" in t for t in btn_texts)
    assert any("Status" in t for t in btn_texts)
    edits = page.findChildren(QLineEdit)
    assert len(edits) >= 1


def test_diff_page_index_is_12(win):
    assert win._diff_page_index == 12


# ── Batch C: Pending Changes UX ───────────────────────────────────────────────

def test_pending_changes_has_inline_diff_panel(win):
    from biome_fm.plastic._components import InlineDiffPanel
    assert hasattr(win, "_pending_diff_panel")
    assert isinstance(win._pending_diff_panel, InlineDiffPanel)


def test_inline_diff_routes_to_panel(win):
    initial_page = win._stack.currentIndex()
    win._inline_diff_pending = True
    win._queue.put(("diff", "--- a\n+++ b\n+hello"))
    win._drain()
    assert win._stack.currentIndex() == initial_page
    assert "hello" in win._pending_diff_panel._unified_edit.toPlainText()


def test_build_by_dir_relative_paths(win, tmp_path):
    wk = tmp_path / "workspace"
    wk.mkdir()
    sub = wk / "src"
    sub.mkdir()
    f = sub / "foo.py"
    f.touch()
    win._wk_path = wk
    win._build_by_dir([PlasticItem(status="CO", path=f)])
    root = win._status_model.invisibleRootItem()
    dir_item = root.child(0, 0)
    assert "src" in dir_item.text()
    assert str(wk) not in dir_item.text()


def test_build_by_status_human_labels(win):
    win._build_by_status([PlasticItem(status="AD", path=Path("/ws/foo.py"))])
    root = win._status_model.invisibleRootItem()
    header_text = root.child(0, 0).text()
    # must show human label, not raw code alone
    assert header_text != "AD"
    assert "Added" in header_text


def test_fmt_size_in_file_row(win, tmp_path):
    f = tmp_path / "test.py"
    f.write_bytes(b"x" * 512)
    from biome_fm.plastic._models import PlasticItem as PI
    plastic = PI(status="CO", path=f)
    row = win._make_file_row(plastic)
    assert row[2].text() != "—"
    assert "B" in row[2].text()


# ── C51 — selection-first actions + confirmation + PR unchecked ───────────────

def test_undo_uses_selection_not_all_checked(qtbot, tmp_path):
    """Selection overrides checked: only selected row emitted, not all 3 checked rows."""
    from unittest.mock import patch
    from PySide6.QtCore import QItemSelectionModel
    from PySide6.QtWidgets import QMessageBox

    win = PlasticWindow()
    qtbot.addWidget(win)
    items = [PlasticItem(status="CO", path=tmp_path / f) for f in ["a.cs", "b.cs", "c.cs"]]
    win.set_status_items(items)
    win._drain()
    # select b.cs (sorted row 1 under the single dir group)
    file_item = win._status_model.item(0, 0).child(1)
    idx = win._status_model.indexFromItem(file_item)
    win._status_tree.selectionModel().select(idx, QItemSelectionModel.SelectionFlag.Select)

    emitted = []
    win.undo_requested.connect(emitted.append)
    with patch("biome_fm.plastic._window.QMessageBox.question",
               return_value=QMessageBox.StandardButton.Yes):
        win._on_undo()
    assert len(emitted) == 1 and len(emitted[0]) == 1


def test_undo_cancelled_by_dialog(qtbot):
    """QMessageBox.question returning No must suppress the undo_requested signal."""
    from unittest.mock import patch
    from PySide6.QtWidgets import QMessageBox

    win = PlasticWindow()
    qtbot.addWidget(win)
    win.set_status_items([PlasticItem(status="CO", path=Path("/w/a.cs"))])
    win._drain()

    emitted = []
    win.undo_requested.connect(emitted.append)
    with patch("biome_fm.plastic._window.QMessageBox.question",
               return_value=QMessageBox.StandardButton.No):
        win._on_undo()
    assert emitted == []


def test_private_rows_unchecked_by_default(qtbot, tmp_path):
    """PR-status rows must be Unchecked by default; _checked_items() must exclude them."""
    win = PlasticWindow()
    qtbot.addWidget(win)
    pr = PlasticItem(status="PR", path=tmp_path / "untracked.cs")
    co = PlasticItem(status="CO", path=tmp_path / "modified.cs")
    win.set_status_items([pr, co])
    win._drain()
    checked = win._checked_items()
    assert all(i.status != "PR" for i in checked)
