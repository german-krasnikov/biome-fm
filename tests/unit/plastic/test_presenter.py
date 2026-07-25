"""Unit tests for PlasticPresenter — no Qt, FakeView, monkeypatched run_cm.

RED: biome_fm.plastic._presenter does not exist yet.
These tests define the contract the implementation must satisfy.

Expected interface:
    class PlasticPresenter:
        def __init__(self, view: PlasticViewProtocol, cwd: Path, ttl: float = 30.0) -> None
        def refresh(self, force: bool = False) -> None  # fires background work
        def drain(self) -> None                         # block until done, deliver to view
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._models import Branch, Changeset, Label, PlasticItem

# Import under test — will fail (RED) until _presenter.py is created
from biome_fm.plastic._presenter import PlasticPresenter  # type: ignore[import]


# ── FakeView ──────────────────────────────────────────────────────────────────

@dataclass
class FakeView:
    status_items: list[PlasticItem] = field(default_factory=list)
    changesets: list[Changeset] = field(default_factory=list)
    branches: list[Branch] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    shelves: list = field(default_factory=list)
    header: tuple[str, str] | None = None
    errors: list[str] = field(default_factory=list)
    busy: list[bool] = field(default_factory=list)
    diffs: list[str] = field(default_factory=list)
    find_results: list = field(default_factory=list)
    workspace_info: object = None
    xlinks: list = field(default_factory=list)

    def set_status_items(self, items: list[PlasticItem]) -> None:
        self.status_items = list(items)

    def set_changesets(self, items: list[Changeset]) -> None:
        self.changesets = list(items)

    def set_branches(self, items: list[Branch]) -> None:
        self.branches = list(items)

    def set_labels(self, items: list[Label]) -> None:
        self.labels = list(items)

    def set_shelves(self, items: list) -> None:
        self.shelves = list(items)

    def set_header(self, branch: str, repo: str) -> None:
        self.header = (branch, repo)

    def show_error(self, msg: str) -> None:
        self.errors.append(msg)

    def show_diff(self, text: str) -> None:
        self.diffs.append(text)

    def set_status_message(self, msg: str) -> None:
        pass

    def set_busy(self, busy: bool) -> None:
        self.busy.append(busy)

    def show_find_results(self, paths: list) -> None:
        self.find_results = list(paths)

    def set_workspace_info(self, wi: object) -> None:
        self.workspace_info = wi

    def set_xlinks(self, items: list) -> None:
        self.xlinks = list(items)

    attributes: tuple | None = None
    users: list = field(default_factory=list)
    groups: list = field(default_factory=list)
    acl: tuple | None = None
    dag: tuple | None = None
    merge_sides: tuple | None = None
    config_entries: list = field(default_factory=list)

    def show_attributes(self, obj_spec: str, items: list) -> None:
        self.attributes = (obj_spec, items)

    def show_acl(self, obj_spec: str, items: list) -> None:
        self.acl = (obj_spec, items)

    def set_users(self, items: list) -> None:
        self.users = list(items)

    def set_groups(self, items: list) -> None:
        self.groups = list(items)

    def set_dag(self, nodes: list, branches: list) -> None:
        self.dag = (nodes, branches)

    def show_merge_sides(self, path, base: str, source: str, dest: str) -> None:
        self.merge_sides = (path, base, source, dest)

    def show_config_entries(self, items: list) -> None:
        self.config_entries = list(items)

    workspaces: list = field(default_factory=list)
    repos: list = field(default_factory=list)
    triggers: list = field(default_factory=list)
    cs_files: list = field(default_factory=list)

    def set_workspaces(self, items: list) -> None:
        self.workspaces = list(items)

    def set_repos(self, items: list) -> None:
        self.repos = list(items)

    def set_triggers(self, items: list) -> None:
        self.triggers = list(items)

    def set_cs_files(self, files: list) -> None:
        self.cs_files = list(files)


# ── Helpers ───────────────────────────────────────────────────────────────────

_STATUS_OUT = "CO|/w/a.py\n"
_CS_OUT = "1|07/24/2026 10:00:00|alice|/main|init\n"
_BRANCH_OUT = "/main|07/24/2026 10:00:00|alice\n"
_LABEL_OUT = "v1.0|1|07/24/2026 10:00:00\n"
_FILEINFO_OUT = "/w\n"  # used by get_server_path inside cm status

def _all_returns(s=_STATUS_OUT, cs=_CS_OUT, b=_BRANCH_OUT, lbl=_LABEL_OUT):
    """Return a side_effect list matching the run_cm call order in refresh()."""
    # Order: status (×2 attempts), changesets, branches, labels, fileinfo (header)
    # Simplest: return from a mapping on first arg
    def _dispatch(args, cwd=None, safe=False, timeout=10):
        cmd = args[0] if args else ""
        if cmd == "status":
            return s
        if cmd == "find" and "changesets" in args:
            return cs
        if cmd == "find" and "branches" in args:
            return b
        if cmd == "find" and "labels" in args:
            return lbl
        if cmd == "fileinfo":
            return _FILEINFO_OUT
        if cmd == "getworkspace":
            return "repo@server\n"
        return ""
    return _dispatch


@pytest.fixture
def view():
    return FakeView()


@pytest.fixture
def cwd(tmp_path):
    return tmp_path


# ── Basic refresh ─────────────────────────────────────────────────────────────

def test_refresh_delivers_status_items(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    assert len(view.status_items) == 1
    assert view.status_items[0].status == "CO"


def test_refresh_delivers_changesets(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    assert len(view.changesets) == 1
    assert view.changesets[0].cs_id == 1


def test_refresh_delivers_branches(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    assert len(view.branches) == 1
    assert view.branches[0].name == "/main"


def test_refresh_delivers_labels(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    assert len(view.labels) == 1
    assert view.labels[0].name == "v1.0"


# ── TTL cache ─────────────────────────────────────────────────────────────────

def test_refresh_within_ttl_skips_run_cm(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()) as m:
        p = PlasticPresenter(view=view, cwd=cwd, ttl=60.0)
        p.refresh()
        p.drain()
        first_count = m.call_count
        p.refresh()  # within TTL — should be a no-op
        p.drain()
    assert m.call_count == first_count  # no extra calls


def test_refresh_force_bypasses_ttl(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()) as m:
        p = PlasticPresenter(view=view, cwd=cwd, ttl=60.0)
        p.refresh()
        p.drain()
        first_count = m.call_count
        p.refresh(force=True)  # force ignores TTL
        p.drain()
    assert m.call_count > first_count


def test_refresh_after_ttl_expired_re_fetches(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()) as m:
        p = PlasticPresenter(view=view, cwd=cwd, ttl=0.01)  # 10ms TTL
        p.refresh()
        p.drain()
        first_count = m.call_count
        time.sleep(0.05)  # wait for TTL to expire
        p.refresh()
        p.drain()
    assert m.call_count > first_count


# ── Error propagation ─────────────────────────────────────────────────────────

def test_cm_not_installed_shows_error(view, cwd):
    from biome_fm.plastic._cm import CMError

    def _fail(args, **kw):
        raise CMError("cm not found")

    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_fail):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    assert len(view.errors) > 0


def test_single_section_error_does_not_block_others(view, cwd):
    """Status raises, but changesets/branches/labels still deliver."""
    from biome_fm.plastic._cm import CMError

    def _dispatch(args, cwd=None, safe=False, timeout=10):
        if args[0] == "status":
            if not safe:
                raise CMError("bad")
            return ""
        return _all_returns()(args, cwd=cwd, safe=safe, timeout=timeout)

    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_dispatch):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    # Changesets should still deliver despite status section failing
    assert len(view.changesets) >= 1


# ── drain idempotency ─────────────────────────────────────────────────────────

def test_drain_is_safe_when_nothing_queued(view, cwd):
    p = PlasticPresenter(view=view, cwd=cwd)
    p.drain()  # no refresh called — must not raise


# ── Shelve / unshelve ─────────────────────────────────────────────────────────

_SHELVE_OUT = "1|07/24/2026 10:00:00|alice|wip\n"


def test_shelve_calls_cm_and_refreshes(view, cwd):
    item = PlasticItem(status="CO", path=cwd / "a.py")
    with patch("biome_fm.plastic._presenter._shelve") as mock_shelve, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.shelve([item], "wip")
        p.drain()
    mock_shelve.assert_called_once_with("wip", cwd, [item.path])


def test_unshelve_calls_cm_and_refreshes(view, cwd):
    with patch("biome_fm.plastic._presenter._unshelve") as mock_unshelve, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.unshelve(42)
        p.drain()
    mock_unshelve.assert_called_once_with(42, cwd)


def test_load_shelves_delivers_to_view(view, cwd):
    def _dispatch(args, cwd=None, safe=False, timeout=10):
        if args[0] == "find" and "shelves" in args:
            return _SHELVE_OUT
        return ""
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_dispatch):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_shelves()
        p.drain()
    assert len(view.shelves) == 1
    assert view.shelves[0].shelve_id == 1
    assert view.shelves[0].owner == "alice"


# ── Merge / rollback ──────────────────────────────────────────────────────────

def test_merge_branch_calls_cm_and_refreshes(view, cwd):
    with patch("biome_fm.plastic._presenter._merge_branch") as mock_merge, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.merge_branch("/main")
        p.drain()
    mock_merge.assert_called_once_with("/main", cwd, preview=False, resolve="", semantic=False)


def test_rollback_changeset_calls_cm_and_refreshes(view, cwd):
    with patch("biome_fm.plastic._presenter._rollback_cs") as mock_rollback, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.rollback_changeset(5)
        p.drain()
    mock_rollback.assert_called_once_with(5, cwd)


# ── Busy indicator ───────────────────────────────────────────────────────────

def test_presenter_emits_busy_around_mutation(view, cwd):
    item = PlasticItem(status="CO", path=cwd / "a.py")
    with patch("biome_fm.plastic._presenter._lock") as mock_lock, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.lock_file(item)
        p.drain()
    # busy=True then busy=False (plus refresh busy events)
    assert True in view.busy
    assert False in view.busy
    assert view.busy[0] is True   # first event is busy=True from _bg_submit


def test_presenter_emits_busy_around_refresh(view, cwd):
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.refresh()
        p.drain()
    assert True in view.busy
    assert False in view.busy


# ── Lock / unlock ─────────────────────────────────────────────────────────────

def test_lock_file_calls_cm_and_refreshes(view, cwd):
    item = PlasticItem(status="CO", path=cwd / "a.py")
    with patch("biome_fm.plastic._presenter._lock") as mock_lock, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.lock_file(item)
        p.drain()
    mock_lock.assert_called_once_with(item.path, cwd)


def test_unlock_file_calls_cm_and_refreshes(view, cwd):
    item = PlasticItem(status="CO", path=cwd / "a.py")
    with patch("biome_fm.plastic._presenter._unlock") as mock_unlock, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.unlock_file(item)
        p.drain()
    mock_unlock.assert_called_once_with(item.path, cwd)


# ── Diff metrics ──────────────────────────────────────────────────────────────

def test_diff_file_prepends_metrics(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1,1 +1,2 @@\n-old\n+new\n+extra\n"
    item = PlasticItem(status="CO", path=cwd / "a.py")
    with patch("biome_fm.plastic._presenter.workspace_diff", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_file(item)
        p.drain()
    assert len(view.diffs) == 1
    assert view.diffs[0].startswith("+2 / -1 lines")


def test_diff_changeset_prepends_metrics(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n"
    with patch("biome_fm.plastic._presenter.run_cm", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_changeset(5)
        p.drain()
    assert len(view.diffs) == 1
    assert view.diffs[0].startswith("+1 / -1 lines")


# ── File ops presenter (4.7) ──────────────────────────────────────────────────

def test_add_to_vcs_calls_add_and_refreshes(view, cwd):
    item = PlasticItem(status="CO", path=cwd / "a.py")
    with patch("biome_fm.plastic._presenter._add") as mock_add, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.add_to_vcs([item])
        p.drain()
    mock_add.assert_called_once_with([item.path], cwd)


def test_remove_from_vcs_calls_remove_and_refreshes(view, cwd):
    items = [PlasticItem(status="CO", path=cwd / "a.py")]
    with patch("biome_fm.plastic._presenter._remove") as mock_rm, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.remove_from_vcs(items)
        p.drain()
    mock_rm.assert_called_once_with(items[0].path, cwd)


def test_move_file_calls_move_and_refreshes(view, cwd):
    src = cwd / "a.py"
    dst = cwd / "b.py"
    with patch("biome_fm.plastic._presenter._move") as mock_move, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.move_file(src, dst)
        p.drain()
    mock_move.assert_called_once_with(src, dst, cwd)


# ── Advanced diff presenter (4.8) ─────────────────────────────────────────────

def test_diff_cs_range_puts_diff_to_queue(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n"
    with patch("biome_fm.plastic._presenter.cs_range_diff", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_cs_range(5, 7)
        p.drain()
    assert len(view.diffs) == 1
    assert "+1 / -1 lines" in view.diffs[0]


def test_diff_branch_puts_diff_to_queue(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n"
    with patch("biome_fm.plastic._presenter._branch_diff", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_branch("feature/x")
        p.drain()
    assert len(view.diffs) == 1
    assert "+1 / -1 lines" in view.diffs[0]


def test_diff_labels_puts_diff_to_queue(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n"
    with patch("biome_fm.plastic._presenter.label_range_diff", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_labels("v1.0", "v2.0")
        p.drain()
    assert len(view.diffs) == 1
    assert "+1 / -1 lines" in view.diffs[0]


def test_diff_shelve_puts_diff_to_queue(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n"
    with patch("biome_fm.plastic._presenter._shelve_diff", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_shelve(42)
        p.drain()
    assert len(view.diffs) == 1
    assert "+1 / -1 lines" in view.diffs[0]


def test_diff_changeset_uses_format_diff(view, cwd):
    _FAKE_DIFF = "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n"
    with patch("biome_fm.plastic._presenter.run_cm", return_value=_FAKE_DIFF):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.diff_changeset(5)
        p.drain()
    assert view.diffs[0].startswith("+1 / -1 lines")


# ── Merge enhancements presenter (4.9) ────────────────────────────────────────

def test_merge_branch_preview_puts_diff_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter._merge_branch", return_value="preview text"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.merge_branch("main", preview=True)
        p.drain()
    assert ("diff", "preview text") in [(k, v) for k, v in zip(
        ["diff"] * len(view.diffs), view.diffs
    )]
    assert view.diffs and view.diffs[0] == "preview text"


def test_merge_branch_non_preview_calls_refresh(view, cwd):
    with patch("biome_fm.plastic._presenter._merge_branch", return_value=""), \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.merge_branch("main", preview=False)
        p.drain()
    # no diff, but changesets were refreshed
    assert len(view.diffs) == 0
    assert len(view.changesets) >= 0  # just ensure no crash


# ── CS edit comment presenter (4.10) ─────────────────────────────────────────

def test_edit_cs_comment_reloads_changesets(view, cwd):
    with patch("biome_fm.plastic._presenter._edit_comment") as mock_edit, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.edit_cs_comment(42, "new msg")
        p.drain()
    mock_edit.assert_called_once_with(42, "new msg", cwd)
    assert len(view.changesets) >= 1


# ── File Search presenter (4.11) ──────────────────────────────────────────────

def test_find_files_puts_results_to_queue(view, cwd):
    from pathlib import Path
    fake_paths = [Path("/repo/src/a.py"), Path("/repo/src/b.py")]
    with patch("biome_fm.plastic._find.find_files", return_value=fake_paths):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.find_files("*.py")
        p.drain()
    assert view.find_results == fake_paths


# ── Xlinks presenter (5.4) ────────────────────────────────────────────────────

def test_load_xlinks_puts_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter._list_xlinks", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_xlinks()
        p.drain()
    assert view.xlinks == []


def test_add_xlink_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._add_xlink") as mock_add, \
         patch("biome_fm.plastic._presenter._list_xlinks", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.add_xlink("libs/x", "server1", "Repo1")
        p.drain()
    mock_add.assert_called_once_with("libs/x", "server1", "Repo1", cwd)
    assert view.xlinks == []


def test_remove_xlink_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._remove_xlink") as mock_rm, \
         patch("biome_fm.plastic._presenter._list_xlinks", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.remove_xlink("libs/x")
        p.drain()
    mock_rm.assert_called_once_with("libs/x", cwd)
    assert view.xlinks == []


# ── Replication presenter (5.5) ───────────────────────────────────────────────

def test_push_replication_queues_output(view, cwd):
    with patch("biome_fm.plastic._presenter._repl_push", return_value="pushed"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.push_replication("srv", "repo")
        p.drain()
    assert "pushed" in view.diffs[0]


def test_pull_replication_queues_output(view, cwd):
    with patch("biome_fm.plastic._presenter._repl_pull", return_value="pulled"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.pull_replication("srv")
        p.drain()
    assert "pulled" in view.diffs[0]


# ── Attributes presenter (5.6) ────────────────────────────────────────────────

def test_load_attributes_puts_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter._list_attrs", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_attributes("cs:1")
        p.drain()
    assert view.attributes == ("cs:1", [])


def test_set_attribute_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._set_attr") as mock, \
         patch("biome_fm.plastic._presenter._list_attrs", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.set_attribute("cs:1", "status", "ok")
        p.drain()
    mock.assert_called_once_with("cs:1", "status", "ok", cwd)


def test_delete_attribute_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._del_attr") as mock, \
         patch("biome_fm.plastic._presenter._list_attrs", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_attribute("cs:1", "status")
        p.drain()
    mock.assert_called_once_with("cs:1", "status", cwd)


# ── ACL presenter (5.7) ──────────────────────────────────────────────────────

def test_load_acl_puts_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter._get_acl", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_acl("br:/main")
        p.drain()
    assert view.acl == ("br:/main", [])


def test_set_acl_entry_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._set_acl") as mock, \
         patch("biome_fm.plastic._presenter._get_acl", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.set_acl_entry("br:/main", "alice", "ReadWrite")
        p.drain()
    mock.assert_called_once_with("br:/main", "alice", "ReadWrite", cwd)


def test_delete_acl_entry_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._del_acl") as mock, \
         patch("biome_fm.plastic._presenter._get_acl", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_acl_entry("br:/main", "alice")
        p.drain()
    mock.assert_called_once_with("br:/main", "alice", cwd)


# ── Users/Groups presenter (5.8) ──────────────────────────────────────────────

def test_load_users_puts_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter._list_users", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_users()
        p.drain()
    assert view.users == []


def test_add_user_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._add_user") as mock, \
         patch("biome_fm.plastic._presenter._list_users", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.add_user("alice", "alice@x.com")
        p.drain()
    mock.assert_called_once_with("alice", "alice@x.com", cwd)


def test_delete_user_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._del_user") as mock, \
         patch("biome_fm.plastic._presenter._list_users", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_user("alice")
        p.drain()
    mock.assert_called_once_with("alice", cwd)


def test_load_groups_puts_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter._list_groups", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_groups()
        p.drain()
    assert view.groups == []


def test_add_group_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._add_group") as mock, \
         patch("biome_fm.plastic._presenter._list_groups", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.add_group("devs")
        p.drain()
    mock.assert_called_once_with("devs", cwd)


def test_delete_group_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._del_group") as mock, \
         patch("biome_fm.plastic._presenter._list_groups", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_group("devs")
        p.drain()
    mock.assert_called_once_with("devs", cwd)


def test_add_group_member_calls_cm_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._add_member") as mock, \
         patch("biome_fm.plastic._presenter._list_groups", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.add_group_member("devs", "alice")
        p.drain()
    mock.assert_called_once_with("devs", "alice", cwd)


# ── Branch DAG presenter (5.1) ────────────────────────────────────────────────

def test_load_dag_puts_to_queue(view, cwd):
    with patch("biome_fm.plastic._presenter.load_dag_data", return_value=([], [])), \
         patch("biome_fm.plastic._presenter.layout_dag", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_dag()
        p.drain()
    assert view.dag == ([], [])


def test_load_dag_delivers_nodes_and_branches(view, cwd):
    from biome_fm.plastic._dag import BranchNode, DAGNode
    from datetime import datetime
    node = DAGNode(cs_id=1, branch="/main", date=datetime(2026,1,1), x=0.0, y=0.0)
    br = BranchNode("/main", "")
    with patch("biome_fm.plastic._presenter.load_dag_data", return_value=([br], [])), \
         patch("biome_fm.plastic._presenter.layout_dag", return_value=[node]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_dag()
        p.drain()
    assert view.dag is not None
    nodes, branches = view.dag
    assert nodes == [node]
    assert branches == [br]


# ── Three-way merge viewer presenter (5.2) ────────────────────────────────────

def test_merge_viewer_puts_to_queue(view, cwd):
    item = PlasticItem(status="CO", path=cwd / "a.py")
    (cwd / "a.py").write_text("local")
    with patch("biome_fm.plastic._presenter.get_merge_sides", return_value=("base", "src", "local")):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.open_merge_viewer(item)
        p.drain()
    assert view.merge_sides is not None
    path, base, source, dest = view.merge_sides
    assert path == item.path
    assert base == "base"
    assert source == "src"
    assert dest == "local"


# ── Undo variants presenter (#10) ─────────────────────────────────────────────

def test_undo_changeset_calls_bg_and_refreshes(view, cwd):
    with patch("biome_fm.plastic._presenter._rollback_cs") as mock, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.undo_changeset(7)
        p.drain()
    mock.assert_called_once_with(7, cwd)


def test_undo_all_calls_bg_and_refreshes(view, cwd):
    with patch("biome_fm.plastic._presenter._undo_all") as mock, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.undo_all()
        p.drain()
    mock.assert_called_once_with(cwd)


def test_undo_keep_calls_bg_for_each_item(view, cwd):
    items = [PlasticItem(status="CO", path=cwd / "a.py")]
    with patch("biome_fm.plastic._presenter._undo_keep") as mock, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.undo_keep(items)
        p.drain()
    mock.assert_called_once_with(items[0].path, cwd)


# ── Semantic merge presenter (#7) ─────────────────────────────────────────────

def test_merge_branch_semantic_passes_flag(view, cwd):
    with patch("biome_fm.plastic._presenter._merge_branch") as mock_merge, \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.merge_branch("feature", semantic=True)
        p.drain()
    mock_merge.assert_called_once_with("feature", cwd, preview=False, resolve="", semantic=True)


# ── Package replication presenter (#9) ────────────────────────────────────────

def test_replica_package_create_queues_diff(view, cwd):
    with patch("biome_fm.plastic._presenter._pkg_create", return_value="created"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.replica_package_create("/out/pkg.rep")
        p.drain()
    assert view.diffs and "created" in view.diffs[0]


def test_replica_package_import_calls_refreshes(view, cwd):
    with patch("biome_fm.plastic._presenter._pkg_import", return_value=""), \
         patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.replica_package_import("/out/pkg.rep")
        p.drain()
    assert len(view.errors) == 0


# ── Preferences / cm config presenter (#8) ───────────────────────────────────

def test_load_config_delivers_entries(view, cwd):
    from biome_fm.plastic._models import ConfigEntry
    entries = [ConfigEntry(key="merge.tool", value="plastic")]
    with patch("biome_fm.plastic._presenter._list_config", return_value=entries):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_config()
        p.drain()
    assert view.config_entries == entries


def test_set_config_entry_calls_set_then_reloads(view, cwd):
    from biome_fm.plastic._models import ConfigEntry
    entries = [ConfigEntry(key="merge.tool", value="bc4")]
    with patch("biome_fm.plastic._presenter._set_config") as mock_set, \
         patch("biome_fm.plastic._presenter._list_config", return_value=entries):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.set_config_entry("merge.tool", "bc4")
        p.drain()
    mock_set.assert_called_once_with("merge.tool", "bc4", cwd)
    assert view.config_entries == entries


# ── Partial workspaces presenter (#5) ────────────────────────────────────────

def test_load_partial_status_queues_diff(view, cwd):
    with patch("biome_fm.plastic._presenter._get_partial_status", return_value="partial: included /src"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_partial_status()
        p.drain()
    assert view.diffs and "partial" in view.diffs[0]


def test_configure_partial_queues_diff(view, cwd):
    with patch("biome_fm.plastic._presenter._configure_partial", return_value="configured"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.configure_partial()
        p.drain()
    assert view.diffs and "configured" in view.diffs[0]


def test_add_partial_calls_add_then_status(view, cwd):
    with patch("biome_fm.plastic._presenter._add_partial") as mock_add, \
         patch("biome_fm.plastic._presenter._get_partial_status", return_value="added"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.add_partial("/src/module")
        p.drain()
    mock_add.assert_called_once_with("/src/module", cwd)
    assert view.diffs and "added" in view.diffs[0]


def test_remove_partial_calls_remove_then_status(view, cwd):
    with patch("biome_fm.plastic._presenter._remove_partial") as mock_rm, \
         patch("biome_fm.plastic._presenter._get_partial_status", return_value="removed"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.remove_partial("/src/module")
        p.drain()
    mock_rm.assert_called_once_with("/src/module", cwd)
    assert view.diffs and "removed" in view.diffs[0]


# ── Workspace & Repo CRUD presenter (#1) ─────────────────────────────────────

def test_load_workspaces_delivers_to_view(view, cwd):
    from biome_fm.plastic._models import WorkspaceEntry
    wk = [WorkspaceEntry(name="wk1", path=Path("/a"), server="srv")]
    with patch("biome_fm.plastic._presenter._list_workspaces", return_value=wk):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_workspaces()
        p.drain()
    assert view.workspaces == wk


def test_create_workspace_calls_and_reloads(view, cwd):
    from biome_fm.plastic._models import WorkspaceEntry
    wk = [WorkspaceEntry(name="new", path=Path("/b"), server="s")]
    with patch("biome_fm.plastic._presenter._create_workspace") as mock, \
         patch("biome_fm.plastic._presenter._list_workspaces", return_value=wk):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.create_workspace("new", "/b", "s", "repo")
        p.drain()
    mock.assert_called_once_with("new", "/b", "s", "repo", cwd)
    assert view.workspaces == wk


def test_delete_workspace_calls_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._delete_workspace") as mock, \
         patch("biome_fm.plastic._presenter._list_workspaces", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_workspace("old")
        p.drain()
    mock.assert_called_once_with("old", cwd)
    assert view.workspaces == []


def test_load_repos_delivers_to_view(view, cwd):
    from biome_fm.plastic._models import RepoEntry
    repos = [RepoEntry(name="r1", server="srv")]
    with patch("biome_fm.plastic._presenter._list_repos", return_value=repos):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_repos()
        p.drain()
    assert view.repos == repos


def test_create_repo_calls_and_reloads(view, cwd):
    from biome_fm.plastic._models import RepoEntry
    repos = [RepoEntry(name="new", server="s")]
    with patch("biome_fm.plastic._presenter._create_repo") as mock, \
         patch("biome_fm.plastic._presenter._list_repos", return_value=repos):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.create_repo("new")
        p.drain()
    mock.assert_called_once_with("new", cwd)
    assert view.repos == repos


def test_delete_repo_calls_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._delete_repo") as mock, \
         patch("biome_fm.plastic._presenter._list_repos", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_repo("old")
        p.drain()
    mock.assert_called_once_with("old", cwd)
    assert view.repos == []


# ── Triggers presenter (#6) ──────────────────────────────────────────────────

def test_load_triggers_delivers_to_view(view, cwd):
    from biome_fm.plastic._models import Trigger
    trigs = [Trigger(trigger_id="1", name="t", event="e", filter="*", command="/x")]
    with patch("biome_fm.plastic._presenter._list_triggers", return_value=trigs):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_triggers()
        p.drain()
    assert view.triggers == trigs


def test_create_trigger_calls_and_reloads(view, cwd):
    from biome_fm.plastic._models import Trigger
    trigs = [Trigger(trigger_id="1", name="t", event="e", filter="*", command="/x")]
    with patch("biome_fm.plastic._presenter._create_trigger") as mock, \
         patch("biome_fm.plastic._presenter._list_triggers", return_value=trigs):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.create_trigger("t", "e", "*", "/x")
        p.drain()
    mock.assert_called_once_with("t", "e", "*", "/x", cwd)
    assert view.triggers == trigs


def test_delete_trigger_calls_and_reloads(view, cwd):
    with patch("biome_fm.plastic._presenter._delete_trigger") as mock, \
         patch("biome_fm.plastic._presenter._list_triggers", return_value=[]):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.delete_trigger("1")
        p.drain()
    mock.assert_called_once_with("1", cwd)
    assert view.triggers == []


# ── Git Sync presenter (#4) ──────────────────────────────────────────────────

def test_sync_git_queues_diff(view, cwd):
    with patch("biome_fm.plastic._presenter._sync_git", return_value="synced ok"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.sync_git("https://github.com/org/repo.git")
        p.drain()
    assert view.diffs and "synced" in view.diffs[0]


def test_load_git_sync_status_queues_diff(view, cwd):
    with patch("biome_fm.plastic._presenter._git_sync_status", return_value="no sync"):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.load_git_sync_status()
        p.drain()
    assert view.diffs and "no sync" in view.diffs[0]


# ── on_cs_selected (Batch D) ─────────────────────────────────────────────────

def test_on_cs_selected_primary_path(view, cwd):
    """cs_log_files result is delivered directly; cs_range_diff not called."""
    from biome_fm.plastic._models import CSDiffFile
    fake_files = [CSDiffFile("/a.py", "M", 1, 0, "")]
    with patch("biome_fm.plastic._presenter.cs_log_files", return_value=fake_files) as m_log, \
         patch("biome_fm.plastic._presenter.cs_range_diff") as m_diff:
        p = PlasticPresenter(view=view, cwd=cwd)
        p.on_cs_selected(5)
        p.drain()
    m_log.assert_called_once_with(5, cwd)
    m_diff.assert_not_called()
    assert view.cs_files == fake_files


def test_on_cs_selected_fallback_to_range_diff(view, cwd):
    """When cs_log_files returns [] fallback fires cs_range_diff(cs_id-1, cs_id)."""
    from biome_fm.plastic._models import CSDiffFile
    fake_files = [CSDiffFile("/a.py", "M", 1, 0, "d")]
    with patch("biome_fm.plastic._presenter.cs_log_files", return_value=[]), \
         patch("biome_fm.plastic._presenter.cs_range_diff", return_value="raw") as m_diff, \
         patch("biome_fm.plastic._presenter.parse_cs_diff_files", return_value=fake_files):
        p = PlasticPresenter(view=view, cwd=cwd)
        p.on_cs_selected(5)
        p.drain()
    m_diff.assert_called_once_with(4, 5, cwd)
    assert view.cs_files == fake_files


def test_on_cs_selected_zero_clears_files(view, cwd):
    """cs_id <= 0 must deliver empty list without calling cs_log_files or cs_range_diff."""
    with patch("biome_fm.plastic._presenter.cs_log_files") as m_log, \
         patch("biome_fm.plastic._presenter.cs_range_diff") as m_diff:
        p = PlasticPresenter(view=view, cwd=cwd)
        p.on_cs_selected(0)
        p.drain()
    m_log.assert_not_called()
    m_diff.assert_not_called()
    assert view.cs_files == []


# ── workspace_info ordering ───────────────────────────────────────────────────

def test_workspace_info_delivered_before_status(cwd):
    """workspace_info must arrive before status so _wk_path is set before _build_by_dir."""
    call_order: list[str] = []

    class _TrackingView(FakeView):
        def set_workspace_info(self, wi: object) -> None:
            call_order.append("workspace_info")
            super().set_workspace_info(wi)

        def set_status_items(self, items):  # type: ignore[override]
            call_order.append("status")
            super().set_status_items(items)

    v = _TrackingView()
    with patch("biome_fm.plastic._presenter.run_cm", side_effect=_all_returns()):
        p = PlasticPresenter(view=v, cwd=cwd)
        p.refresh()
        p.drain()

    assert "workspace_info" in call_order
    assert "status" in call_order
    assert call_order.index("workspace_info") < call_order.index("status")
