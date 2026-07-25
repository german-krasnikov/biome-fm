"""PlasticPresenter — Qt-free logic layer. Drives PlasticViewProtocol from a background thread.

Usage pattern (matches test contract and Qt production use):
    p.refresh()   — fires background work
    p.drain()     — waits for completion, pushes results to view (called by QTimer or test)
"""
from __future__ import annotations

import queue
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from ._annotate import get_blame
from ._branches import delete_branch as _delete_branch
from ._branches import parse_branches
from ._branches import rename_branch as _rename_branch
from ._branches import switch_branch as _switch_branch
from ._branches import switch_changeset as _switch_cs
from ._changelist import (
    add_to_changelist,
    parse_changelist_status,
)
from ._changelist import (
    delete_changelist as _delete_changelist,
)
from ._changesets import checkin as _checkin
from ._changesets import edit_comment as _edit_comment
from ._changesets import parse_changesets
from ._changesets import rollback_changeset as _rollback_cs
from ._changesets import undo as _undo
from ._changesets import undo_all as _undo_all
from ._changesets import undo_keep as _undo_keep
from ._changesets import update as _update
from ._cm import run_cm
from ._dag import load_dag_data, layout_dag
from ._diff import (
    branch_diff as _branch_diff,
)
from ._diff import (
    count_diff_lines,
    cs_log_files,
    cs_range_diff,
    get_merge_sides,
    label_range_diff,
    parse_cs_diff_files,
    workspace_diff,
)
from ._diff import (
    shelve_diff as _shelve_diff,
)
from ._fileops import add as _add
from ._fileops import move as _move
from ._fileops import remove as _remove
from ._history import get_file_history
from ._labels import create_label as _create_label
from ._labels import delete_label as _delete_label
from ._labels import parse_labels
from ._labels import rename_label as _rename_label
from ._lock import lock as _lock
from ._lock import unlock as _unlock
from ._merge import merge_branch as _merge_branch
from ._models import PlasticItem
from ._reviews import (
    create_review as _create_review,
)
from ._reviews import (
    delete_review as _delete_review,
)
from ._reviews import (
    edit_review_status as _edit_review_status,
)
from ._reviews import (
    parse_reviews,
)
from ._shelve import parse_shelves
from ._xlinks import list_xlinks as _list_xlinks, add_xlink as _add_xlink, remove_xlink as _remove_xlink
from ._replication import replication_push as _repl_push, replication_pull as _repl_pull
from ._replication import package_create as _pkg_create, package_import as _pkg_import
from ._attributes import list_attributes as _list_attrs, set_attribute as _set_attr, delete_attribute as _del_attr
from ._acl import get_acl as _get_acl, set_acl as _set_acl, delete_acl as _del_acl
from ._users import list_users as _list_users, add_user as _add_user, delete_user as _del_user
from ._users import list_groups as _list_groups, add_group as _add_group, delete_group as _del_group, add_group_member as _add_member
from ._shelve import shelve as _shelve
from ._shelve import unshelve as _unshelve
from ._status import parse_status
from ._config import list_config as _list_config, set_config as _set_config
from ._partial import (
    get_partial_status as _get_partial_status,
    configure_partial as _configure_partial,
    add_partial as _add_partial,
    remove_partial as _remove_partial,
)
from ._workspace_mgmt import (
    list_workspaces as _list_workspaces,
    create_workspace as _create_workspace,
    delete_workspace as _delete_workspace,
    list_repos as _list_repos,
    create_repo as _create_repo,
    delete_repo as _delete_repo,
)
from ._triggers import (
    list_triggers as _list_triggers,
    create_trigger as _create_trigger,
    delete_trigger as _delete_trigger,
)
from ._git_sync import sync_git as _sync_git, git_sync_status as _git_sync_status
from ._window import PlasticViewProtocol

# Format strings mirrored from sub-modules so run_cm calls stay in this namespace
# (enables patching biome_fm.plastic._presenter.run_cm in tests)
_CS_FMT = "{changesetid}|{date}|{owner}|{branch}|{comment}"
_BR_FMT = "{name}|{date}|{owner}"
_LBL_FMT = "{name}|{changeset}|{date}"
_SHELVE_FMT = "{id}|{date}|{owner}|{comment}"
_REVIEW_FMT = "{id}|{status}|{assignee}|{date}|{title}"


class PlasticPresenter:
    """All cm operations run on a single background thread.

    refresh() fires background work; drain() waits for it and delivers to view.
    drain() blocks on a pending refresh() future so tests can call it synchronously.
    In production a QTimer(100ms) calls drain() — cm commands are typically < 500ms.
    """

    def __init__(self, view: PlasticViewProtocol, cwd: Path, ttl: float = 30.0) -> None:
        self._view = view
        self._cwd = cwd
        self._ttl = ttl
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="plastic")
        self._queue: queue.SimpleQueue[tuple[str, Any]] = queue.SimpleQueue()
        self._last_refresh: float = 0.0
        self._future: Future | None = None  # type: ignore[type-arg]

    # ── Primary read: refresh all tabs ────────────────────────────────────────

    def refresh(self, force: bool = False) -> None:
        """Fire background refresh. Skips if within TTL unless force=True."""
        now = time.monotonic()
        if not force and now - self._last_refresh < self._ttl:
            return
        self._last_refresh = now
        self._future = self._pool.submit(self._bg_refresh)

    def _bg_refresh(self) -> None:
        """Load all four data sets; each section has its own try/except so one
        failure (e.g. cm unavailable for status) doesn't block the others."""
        self._queue.put(("busy", True))
        try:
            # workspace_info MUST be first — sets _wk_path before status items are rendered
            try:
                from ._workspace import get_workspace_info
                wi = get_workspace_info(self._cwd)
                self._queue.put(("workspace_info", wi))
            except Exception as exc:
                self._queue.put(("error", str(exc)))

            try:
                out = run_cm(["status", "--all", "--machinereadable"], cwd=self._cwd, safe=True)
                if not out.strip():
                    out = run_cm(["status", "--all"], cwd=self._cwd, safe=True)
                self._queue.put(("status", parse_status(out, self._cwd)))
            except Exception as exc:
                self._queue.put(("error", str(exc)))

            try:
                out = run_cm(["find", "changesets", f"--format={_CS_FMT}"], cwd=self._cwd, safe=True)
                css = parse_changesets(out)
                self._queue.put(("changesets", css))
                if css:
                    self._queue.put(("header", (css[-1].branch, self._cwd.name)))
            except Exception as exc:
                self._queue.put(("error", str(exc)))

            try:
                out = run_cm(["find", "branches", f"--format={_BR_FMT}"], cwd=self._cwd, safe=True)
                self._queue.put(("branches", parse_branches(out)))
            except Exception as exc:
                self._queue.put(("error", str(exc)))

            try:
                out = run_cm(["find", "labels", f"--format={_LBL_FMT}"], cwd=self._cwd, safe=True)
                self._queue.put(("labels", parse_labels(out)))
            except Exception as exc:
                self._queue.put(("error", str(exc)))
        finally:
            self._queue.put(("busy", False))

    # ── Drain ─────────────────────────────────────────────────────────────────

    def drain(self) -> None:
        """Push queued results to view. Waits for a pending refresh() to finish first."""
        if self._future is not None and not self._future.done():
            self._future.result()  # blocks until background refresh completes
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                match kind:
                    case "status":     self._view.set_status_items(payload)
                    case "changesets": self._view.set_changesets(payload)
                    case "branches":   self._view.set_branches(payload)
                    case "labels":     self._view.set_labels(payload)
                    case "shelves":    self._view.set_shelves(payload)
                    case "header":     self._view.set_header(*payload)
                    case "error":      self._view.show_error(payload)
                    case "diff":       self._view.show_diff(payload)
                    case "busy":       self._view.set_busy(payload)  # type: ignore[arg-type]
                    case "history":
                        path, revisions = payload   # type: ignore[misc]
                        self._view.show_history(path, revisions)
                    case "blame":
                        path, lines = payload       # type: ignore[misc]
                        self._view.show_blame(path, lines)
                    case "reviews":
                        self._view.set_reviews(payload)  # type: ignore[arg-type]
                    case "changelist_status":
                        self._view.set_changelist_status(payload)  # type: ignore[arg-type]
                    case "workspace_info":
                        self._view.set_workspace_info(payload)  # type: ignore[arg-type]
                    case "find_results":
                        self._view.show_find_results(payload)  # type: ignore[arg-type]
                    case "xlinks":
                        self._view.set_xlinks(payload)  # type: ignore[arg-type]
                    case "attributes":
                        obj_spec, items = payload  # type: ignore[misc]
                        self._view.show_attributes(obj_spec, items)  # type: ignore[arg-type]
                    case "acl":
                        obj_spec, items = payload  # type: ignore[misc]
                        self._view.show_acl(obj_spec, items)  # type: ignore[arg-type]
                    case "users":
                        self._view.set_users(payload)  # type: ignore[arg-type]
                    case "groups":
                        self._view.set_groups(payload)  # type: ignore[arg-type]
                    case "dag":
                        nodes, branches = payload  # type: ignore[misc]
                        self._view.set_dag(nodes, branches)  # type: ignore[arg-type]
                    case "merge_sides":
                        path, base, source, dest = payload  # type: ignore[misc]
                        self._view.show_merge_sides(path, base, source, dest)  # type: ignore[arg-type]
                    case "config_entries":
                        self._view.show_config_entries(payload)  # type: ignore[arg-type]
                    case "workspaces":
                        self._view.set_workspaces(payload)  # type: ignore[arg-type]
                    case "repos":
                        self._view.set_repos(payload)  # type: ignore[arg-type]
                    case "triggers":
                        self._view.set_triggers(payload)  # type: ignore[arg-type]
        except queue.Empty:
            pass

    # ── Individual tab refreshes ──────────────────────────────────────────────

    def refresh_status(self) -> None:
        self.refresh(force=True)

    def load_changesets(self) -> None:
        def _run() -> None:
            out = run_cm(["find", "changesets", f"--format={_CS_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("changesets", parse_changesets(out)))
        self._bg_submit(_run)

    def load_branches(self) -> None:
        def _run() -> None:
            out = run_cm(["find", "branches", f"--format={_BR_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("branches", parse_branches(out)))
        self._bg_submit(_run)

    def load_labels(self) -> None:
        def _run() -> None:
            out = run_cm(["find", "labels", f"--format={_LBL_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("labels", parse_labels(out)))
        self._bg_submit(_run)

    # ── Mutations — call sub-module helpers; auto-refresh after ───────────────

    def checkin(self, items: list[PlasticItem], msg: str) -> None:
        paths = [item.path for item in items] if items else None
        def _run() -> None:
            _checkin(msg, self._cwd, paths)
            self._bg_refresh()
        self._bg_submit(_run)

    def undo(self, items: list[PlasticItem]) -> None:
        def _run() -> None:
            for item in items:
                _undo(item.path, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def update(self) -> None:
        def _run() -> None:
            _update(self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def switch_branch(self, name: str) -> None:
        def _run() -> None:
            _switch_branch(name, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def switch_changeset(self, cs_id: int) -> None:
        def _run() -> None:
            _switch_cs(cs_id, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def switch_label(self, name: str) -> None:
        def _run() -> None:
            run_cm(["switch", f"lb:{name}"], cwd=self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def create_branch(self, name: str) -> None:
        def _run() -> None:
            run_cm(["branch", "create", name], cwd=self._cwd)
            out = run_cm(["find", "branches", f"--format={_BR_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("branches", parse_branches(out)))
        self._bg_submit(_run)

    @staticmethod
    def _format_diff(out: str, fallback: str) -> str:
        if out and not out.startswith("("):
            added, removed = count_diff_lines(out)
            return f"+{added} / -{removed} lines\n\n" + out
        return out or fallback

    def diff_file(self, item: PlasticItem) -> None:
        def _run() -> None:
            diff = workspace_diff(item.path, self._cwd)
            self._queue.put(("diff", self._format_diff(diff, "(no local changes)")))
        self._bg_submit(_run)

    def diff_changeset(self, cs_id: int) -> None:
        """Diff cs_id vs its predecessor via `cm diff cs:N-1..cs:N`."""
        def _run() -> None:
            out = run_cm(["diff", f"cs:{cs_id - 1}..cs:{cs_id}"], cwd=self._cwd, safe=True)
            self._queue.put(("diff", self._format_diff(out, f"(no diff available for cs:{cs_id})")))
        self._bg_submit(_run)

    def on_cs_selected(self, cs_id: int) -> None:
        """Load per-file diff list for the selected changeset (async)."""
        def _load() -> None:
            if cs_id <= 0:
                self._view.set_cs_files([])
                return
            files = cs_log_files(cs_id, self._cwd)
            if not files:
                # Fallback: cloud workspaces without cm log support
                diff_text = cs_range_diff(cs_id - 1, cs_id, self._cwd)
                files = parse_cs_diff_files(diff_text)
            self._view.set_cs_files(files)
        self._bg_submit(_load)

    def diff_cs_range(self, cs_a: int, cs_b: int) -> None:
        def _run() -> None:
            out = cs_range_diff(cs_a, cs_b, self._cwd)
            self._queue.put(("diff", self._format_diff(out, f"(no diff for cs:{cs_a}..cs:{cs_b})")))
        self._bg_submit(_run)

    def diff_branch(self, name: str) -> None:
        def _run() -> None:
            out = _branch_diff(name, self._cwd)
            self._queue.put(("diff", self._format_diff(out, f"(no diff for br:{name})")))
        self._bg_submit(_run)

    def diff_labels(self, lb_a: str, lb_b: str) -> None:
        def _run() -> None:
            out = label_range_diff(lb_a, lb_b, self._cwd)
            self._queue.put(("diff", self._format_diff(out, f"(no diff for lb:{lb_a}..lb:{lb_b})")))
        self._bg_submit(_run)

    def diff_shelve(self, shelve_id: int) -> None:
        def _run() -> None:
            out = _shelve_diff(shelve_id, self._cwd)
            self._queue.put(("diff", self._format_diff(out, f"(no diff for sh:{shelve_id})")))
        self._bg_submit(_run)

    def shelve(self, items: list[PlasticItem], msg: str) -> None:
        paths = [item.path for item in items] if items else None
        def _run() -> None:
            _shelve(msg, self._cwd, paths)
            self._bg_refresh()
        self._bg_submit(_run)

    def unshelve(self, shelve_id: int) -> None:
        def _run() -> None:
            _unshelve(shelve_id, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def load_shelves(self) -> None:
        def _run() -> None:
            out = run_cm(["find", "shelves", f"--format={_SHELVE_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("shelves", parse_shelves(out)))
        self._bg_submit(_run)

    def merge_branch(self, name: str, preview: bool = False, resolve: str = "",
                     semantic: bool = False) -> None:
        def _run() -> None:
            out = _merge_branch(name, self._cwd, preview=preview, resolve=resolve, semantic=semantic)
            if preview:
                self._queue.put(("diff", out or "(nothing to merge)"))
            else:
                self._bg_refresh()
        self._bg_submit(_run)

    def undo_changeset(self, cs_id: int) -> None:
        def _run() -> None:
            _rollback_cs(cs_id, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def undo_all(self) -> None:
        def _run() -> None:
            _undo_all(self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def undo_keep(self, items: list[PlasticItem]) -> None:
        def _run() -> None:
            for item in items:
                _undo_keep(item.path, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def create_label(self, name: str, cs_id: int) -> None:
        def _run() -> None:
            _create_label(name, cs_id, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def delete_label(self, name: str) -> None:
        def _run() -> None:
            _delete_label(name, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def rename_label(self, old: str, new: str) -> None:
        def _run() -> None:
            _rename_label(old, new, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def delete_branch(self, name: str) -> None:
        def _run() -> None:
            _delete_branch(name, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def rename_branch(self, old: str, new: str) -> None:
        def _run() -> None:
            _rename_branch(old, new, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def rollback_changeset(self, cs_id: int) -> None:
        def _run() -> None:
            _rollback_cs(cs_id, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def lock_file(self, item: PlasticItem) -> None:
        def _run() -> None:
            _lock(item.path, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def unlock_file(self, item: PlasticItem) -> None:
        def _run() -> None:
            _unlock(item.path, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def add_to_vcs(self, items: list[PlasticItem]) -> None:
        def _run() -> None:
            _add([i.path for i in items], self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def remove_from_vcs(self, items: list[PlasticItem]) -> None:
        def _run() -> None:
            for i in items:
                _remove(i.path, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def move_file(self, src: Path, dst: Path) -> None:
        def _run() -> None:
            _move(src, dst, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def edit_cs_comment(self, cs_id: int, comment: str) -> None:
        def _run() -> None:
            _edit_comment(cs_id, comment, self._cwd)
            out = run_cm(["find", "changesets", f"--format={_CS_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("changesets", parse_changesets(out)))
        self._bg_submit(_run)

    def file_history(self, item: PlasticItem) -> None:
        def _run() -> None:
            revisions = get_file_history(item.path, self._cwd)
            self._queue.put(("history", (item.path, revisions)))
        self._bg_submit(_run)

    def blame_file(self, item: PlasticItem) -> None:
        def _run() -> None:
            lines = get_blame(item.path, self._cwd)
            self._queue.put(("blame", (item.path, lines)))
        self._bg_submit(_run)

    # ── Reviews ───────────────────────────────────────────────────────────────

    def load_reviews(self) -> None:
        def _run() -> None:
            out = run_cm(["find", "reviews", f"--format={_REVIEW_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("reviews", parse_reviews(out)))
        self._bg_submit(_run)

    def create_review(self, cs_id: int, title: str, assignee: str = "",
                      status: str = "Under review") -> None:
        def _run() -> None:
            _create_review(cs_id, title, self._cwd, assignee=assignee, status=status)
            out = run_cm(["find", "reviews", f"--format={_REVIEW_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("reviews", parse_reviews(out)))
        self._bg_submit(_run)

    def edit_review_status(self, review_id: int, status: str) -> None:
        def _run() -> None:
            _edit_review_status(review_id, status, self._cwd)
            out = run_cm(["find", "reviews", f"--format={_REVIEW_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("reviews", parse_reviews(out)))
        self._bg_submit(_run)

    def delete_review(self, review_id: int) -> None:
        def _run() -> None:
            _delete_review(review_id, self._cwd)
            out = run_cm(["find", "reviews", f"--format={_REVIEW_FMT}"], cwd=self._cwd, safe=True)
            self._queue.put(("reviews", parse_reviews(out)))
        self._bg_submit(_run)

    # ── Changelists ───────────────────────────────────────────────────────────

    def load_changelist_status(self) -> None:
        def _run() -> None:
            out = run_cm(["status", "--changelists"], cwd=self._cwd, safe=True)
            self._queue.put(("changelist_status", parse_changelist_status(out, self._cwd)))
        self._bg_submit(_run)

    def delete_changelist(self, name: str) -> None:
        def _run() -> None:
            _delete_changelist(name, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    def move_to_changelist(self, items: list[PlasticItem], name: str) -> None:
        def _run() -> None:
            add_to_changelist(name, [i.path for i in items], self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    # ── File Search (4.11) ────────────────────────────────────────────────────

    def find_files(self, pattern: str) -> None:
        def _run() -> None:
            from ._find import find_files as _find_files
            paths = _find_files(pattern, self._cwd)
            self._queue.put(("find_results", paths))
        self._bg_submit(_run)

    # ── Xlinks (5.4) ─────────────────────────────────────────────────────────

    def load_xlinks(self) -> None:
        def _run() -> None:
            self._queue.put(("xlinks", _list_xlinks(self._cwd)))
        self._bg_submit(_run)

    def add_xlink(self, path: str, server: str, repo: str) -> None:
        def _run() -> None:
            _add_xlink(path, server, repo, self._cwd)
            self._queue.put(("xlinks", _list_xlinks(self._cwd)))
        self._bg_submit(_run)

    def remove_xlink(self, path: str) -> None:
        def _run() -> None:
            _remove_xlink(path, self._cwd)
            self._queue.put(("xlinks", _list_xlinks(self._cwd)))
        self._bg_submit(_run)

    # ── Replication (5.5) ─────────────────────────────────────────────────────

    def push_replication(self, server: str, repo: str) -> None:
        def _run() -> None:
            out = _repl_push(server, repo, self._cwd)
            self._queue.put(("diff", out))
        self._bg_submit(_run)

    def pull_replication(self, server: str) -> None:
        def _run() -> None:
            out = _repl_pull(server, self._cwd)
            self._queue.put(("diff", out))
        self._bg_submit(_run)

    def replica_package_create(self, output_path: str) -> None:
        def _run() -> None:
            out = _pkg_create(output_path, self._cwd)
            self._queue.put(("diff", out or "Package created."))
        self._bg_submit(_run)

    def replica_package_import(self, file_path: str) -> None:
        def _run() -> None:
            _pkg_import(file_path, self._cwd)
            self._bg_refresh()
        self._bg_submit(_run)

    # ── Attributes (5.6) ──────────────────────────────────────────────────────

    def load_attributes(self, obj_spec: str) -> None:
        def _run() -> None:
            items = _list_attrs(obj_spec, self._cwd)
            self._queue.put(("attributes", (obj_spec, items)))
        self._bg_submit(_run)

    def set_attribute(self, obj_spec: str, name: str, value: str) -> None:
        def _run() -> None:
            _set_attr(obj_spec, name, value, self._cwd)
            items = _list_attrs(obj_spec, self._cwd)
            self._queue.put(("attributes", (obj_spec, items)))
        self._bg_submit(_run)

    def delete_attribute(self, obj_spec: str, name: str) -> None:
        def _run() -> None:
            _del_attr(obj_spec, name, self._cwd)
            items = _list_attrs(obj_spec, self._cwd)
            self._queue.put(("attributes", (obj_spec, items)))
        self._bg_submit(_run)

    # ── ACL (5.7) ─────────────────────────────────────────────────────────────

    def load_acl(self, obj_spec: str) -> None:
        def _run() -> None:
            items = _get_acl(obj_spec, self._cwd)
            self._queue.put(("acl", (obj_spec, items)))
        self._bg_submit(_run)

    def set_acl_entry(self, obj_spec: str, principal: str, permission: str) -> None:
        def _run() -> None:
            _set_acl(obj_spec, principal, permission, self._cwd)
            items = _get_acl(obj_spec, self._cwd)
            self._queue.put(("acl", (obj_spec, items)))
        self._bg_submit(_run)

    def delete_acl_entry(self, obj_spec: str, principal: str) -> None:
        def _run() -> None:
            _del_acl(obj_spec, principal, self._cwd)
            items = _get_acl(obj_spec, self._cwd)
            self._queue.put(("acl", (obj_spec, items)))
        self._bg_submit(_run)

    # ── Users / Groups (5.8) ──────────────────────────────────────────────────

    def load_users(self) -> None:
        def _run() -> None:
            self._queue.put(("users", _list_users(self._cwd)))
        self._bg_submit(_run)

    def add_user(self, name: str, email: str) -> None:
        def _run() -> None:
            _add_user(name, email, self._cwd)
            self._queue.put(("users", _list_users(self._cwd)))
        self._bg_submit(_run)

    def delete_user(self, name: str) -> None:
        def _run() -> None:
            _del_user(name, self._cwd)
            self._queue.put(("users", _list_users(self._cwd)))
        self._bg_submit(_run)

    def load_groups(self) -> None:
        def _run() -> None:
            self._queue.put(("groups", _list_groups(self._cwd)))
        self._bg_submit(_run)

    def add_group(self, name: str) -> None:
        def _run() -> None:
            _add_group(name, self._cwd)
            self._queue.put(("groups", _list_groups(self._cwd)))
        self._bg_submit(_run)

    def delete_group(self, name: str) -> None:
        def _run() -> None:
            _del_group(name, self._cwd)
            self._queue.put(("groups", _list_groups(self._cwd)))
        self._bg_submit(_run)

    def add_group_member(self, group: str, user: str) -> None:
        def _run() -> None:
            _add_member(group, user, self._cwd)
            self._queue.put(("groups", _list_groups(self._cwd)))
        self._bg_submit(_run)

    # ── Branch DAG (5.1) ──────────────────────────────────────────────────────

    def load_dag(self) -> None:
        def _run() -> None:
            branches, changesets = load_dag_data(self._cwd)
            nodes = layout_dag(branches, changesets)
            self._queue.put(("dag", (nodes, branches)))
        self._bg_submit(_run)

    # ── Three-way merge viewer (5.2) ──────────────────────────────────────────

    def open_merge_viewer(self, item: PlasticItem) -> None:
        def _run() -> None:
            base, source, dest = get_merge_sides(item.path, self._cwd)
            self._queue.put(("merge_sides", (item.path, base, source, dest)))
        self._bg_submit(_run)

    # ── Preferences / cm config (#8) ─────────────────────────────────────────

    def load_config(self) -> None:
        def _run() -> None:
            items = _list_config(self._cwd)
            self._queue.put(("config_entries", items))
        self._bg_submit(_run)

    def set_config_entry(self, key: str, value: str) -> None:
        def _run() -> None:
            _set_config(key, value, self._cwd)
            items = _list_config(self._cwd)
            self._queue.put(("config_entries", items))
        self._bg_submit(_run)

    # ── Partial workspaces (#5) ───────────────────────────────────────────────

    def load_partial_status(self) -> None:
        def _run() -> None:
            out = _get_partial_status(self._cwd)
            self._queue.put(("diff", out or "(no partial configuration)"))
        self._bg_submit(_run)

    def configure_partial(self) -> None:
        def _run() -> None:
            out = _configure_partial(self._cwd)
            self._queue.put(("diff", out or "Partial workspace configured."))
        self._bg_submit(_run)

    def add_partial(self, path: str) -> None:
        def _run() -> None:
            _add_partial(path, self._cwd)
            out = _get_partial_status(self._cwd)
            self._queue.put(("diff", out or f"Added: {path}"))
        self._bg_submit(_run)

    def remove_partial(self, path: str) -> None:
        def _run() -> None:
            _remove_partial(path, self._cwd)
            out = _get_partial_status(self._cwd)
            self._queue.put(("diff", out or f"Removed: {path}"))
        self._bg_submit(_run)

    # ── Workspaces & Repos (#1) ───────────────────────────────────────────────

    def load_workspaces(self) -> None:
        def _run() -> None:
            self._queue.put(("workspaces", _list_workspaces(self._cwd)))
        self._bg_submit(_run)

    def create_workspace(self, name: str, path: str, server: str, repo: str) -> None:
        def _run() -> None:
            _create_workspace(name, path, server, repo, self._cwd)
            self._queue.put(("workspaces", _list_workspaces(self._cwd)))
        self._bg_submit(_run)

    def delete_workspace(self, name: str) -> None:
        def _run() -> None:
            _delete_workspace(name, self._cwd)
            self._queue.put(("workspaces", _list_workspaces(self._cwd)))
        self._bg_submit(_run)

    def load_repos(self) -> None:
        def _run() -> None:
            self._queue.put(("repos", _list_repos(self._cwd)))
        self._bg_submit(_run)

    def create_repo(self, name: str) -> None:
        def _run() -> None:
            _create_repo(name, self._cwd)
            self._queue.put(("repos", _list_repos(self._cwd)))
        self._bg_submit(_run)

    def delete_repo(self, name: str) -> None:
        def _run() -> None:
            _delete_repo(name, self._cwd)
            self._queue.put(("repos", _list_repos(self._cwd)))
        self._bg_submit(_run)

    # ── Triggers (#6) ────────────────────────────────────────────────────────

    def load_triggers(self) -> None:
        def _run() -> None:
            self._queue.put(("triggers", _list_triggers(self._cwd)))
        self._bg_submit(_run)

    def create_trigger(self, name: str, event: str, filter_: str, command: str) -> None:
        def _run() -> None:
            _create_trigger(name, event, filter_, command, self._cwd)
            self._queue.put(("triggers", _list_triggers(self._cwd)))
        self._bg_submit(_run)

    def delete_trigger(self, trigger_id: str) -> None:
        def _run() -> None:
            _delete_trigger(trigger_id, self._cwd)
            self._queue.put(("triggers", _list_triggers(self._cwd)))
        self._bg_submit(_run)

    # ── Git Sync (#4) ─────────────────────────────────────────────────────────

    def sync_git(self, url: str) -> None:
        def _run() -> None:
            out = _sync_git(url, self._cwd)
            self._queue.put(("diff", out or "Sync complete."))
        self._bg_submit(_run)

    def load_git_sync_status(self) -> None:
        def _run() -> None:
            out = _git_sync_status(self._cwd)
            self._queue.put(("diff", out or "(no git sync configured)"))
        self._bg_submit(_run)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _bg_submit(self, fn) -> None:  # type: ignore[type-arg]
        """Submit *fn* to pool; catch any exception and forward to view as error."""
        def _wrapper() -> None:
            self._queue.put(("busy", True))
            try:
                fn()
            except Exception as exc:
                self._queue.put(("error", str(exc)))
            finally:
                self._queue.put(("busy", False))
        self._future = self._pool.submit(_wrapper)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
