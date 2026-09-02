"""PlasticPlugin — hookimpl class for the Plastic SCM biome-fm plugin."""
from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.registry import CommandEntry
from biome_fm.plugins.hookspecs import hookimpl
from biome_fm.plugins.types import ActionSpec

from ._models import PlasticItem


def _undo_with_confirm(presenter: object, pi: list) -> None:
    from PySide6.QtWidgets import QApplication, QMessageBox
    n = len(pi)
    if QMessageBox.question(
        QApplication.activeWindow(), "Undo Changes",
        f"Revert {n} file{'s' if n != 1 else ''}? This cannot be undone.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    ) == QMessageBox.StandardButton.Yes:
        presenter.undo(pi)  # type: ignore[union-attr]


class PlasticPlugin:
    BIOME_FM_API_VERSION = (1, 0)

    def __init__(self) -> None:
        self._current_repo: Path | None = None
        self._active_path_fn: Callable[[], Path] | None = None
        # root → (PlasticWindow, PlasticPresenter)
        self._windows: dict[Path, tuple] = {}

    @staticmethod
    def _find_repo(path: Path) -> Path | None:
        """Walk *path* and its parents looking for a .plastic/ directory."""
        for p in [path, *path.parents]:
            if (p / ".plastic").is_dir():
                return p
        return None

    @hookimpl
    def on_navigate(self, path: Path) -> None:
        # Always update repo detection — don't gate on cm availability here;
        # context_menu_actions tests expect _current_repo set regardless of cm.
        self._current_repo = self._find_repo(path)

    @hookimpl
    def register_commands(self, registry: object) -> None:
        if not shutil.which("cm"):
            return
        registry.register(  # type: ignore[union-attr]
            CommandEntry(
                name="plastic.open",
                shortcut="Ctrl+Shift+P",
                callback=self._open_window,
            )
        )

    @hookimpl
    def context_menu_actions(self, items: list[object], pane_id: str) -> list[ActionSpec]:
        if not self._current_repo:
            return []
        # Basic actions open the window (no cm call needed here)
        result: list[ActionSpec] = [
            ActionSpec("Plastic SCM…", callback=self._open_window, separator_before=True),
            ActionSpec("Plastic: Checkin…", callback=self._open_window),
        ]
        # Per-file diff/undo only if the window (and its presenter) is already open
        root = self._current_repo
        if root in self._windows and items:
            _, presenter = self._windows[root]
            file_paths = [
                i.path  # type: ignore[union-attr]
                for i in items
                if hasattr(i, "path") and not getattr(i, "is_dir", True)
            ]
            if file_paths:
                plastic_items = [PlasticItem(status="CO", path=p) for p in file_paths]
                result += [
                    ActionSpec(
                        "Plastic: Diff",
                        callback=lambda i=plastic_items[0]: presenter.diff_file(i),
                    ),
                    ActionSpec(
                        "Plastic: Undo",
                        callback=lambda pi=plastic_items: _undo_with_confirm(presenter, pi),
                    ),
                ]
        return result

    def _open_window(self) -> None:
        if not shutil.which("cm"):
            return
        root = self._current_repo
        if root is None and self._active_path_fn:
            try:
                root = self._find_repo(self._active_path_fn())
            except Exception:
                pass
        if root is None:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            path = QFileDialog.getExistingDirectory(None, "Select Plastic SCM workspace")
            if not path:
                return
            root = self._find_repo(Path(path))
            if root is None:
                QMessageBox.warning(None, "Plastic SCM", "No .plastic/ directory found.")
                return
            self._current_repo = root
        if root in self._windows:
            win, _ = self._windows[root]
            win.show()  # type: ignore[union-attr]
            win.raise_()  # type: ignore[union-attr]
            return

        from ._presenter import PlasticPresenter
        from ._window import PlasticWindow

        win = PlasticWindow()
        p = PlasticPresenter(win, root)

        # Wire all Window signals → presenter methods
        win.update_requested.connect(p.update)
        win.refresh_changes.connect(p.refresh_status)
        win.checkin_requested.connect(p.checkin)
        win.undo_requested.connect(p.undo)
        win.diff_file_requested.connect(p.diff_file)
        win.refresh_changesets.connect(p.load_changesets)
        win.switch_to_cs.connect(p.switch_changeset)
        win.diff_with_prev.connect(p.diff_changeset)
        win.cs_double_clicked.connect(p.switch_changeset)
        win.cs_selected.connect(p.on_cs_selected)
        win.refresh_branches.connect(p.load_branches)
        win.switch_branch.connect(p.switch_branch)
        win.create_branch_requested.connect(p.create_branch)
        win.refresh_labels.connect(p.load_labels)
        win.switch_to_label.connect(p.switch_label)
        win.create_label_requested.connect(p.create_label)
        win.delete_label_requested.connect(p.delete_label)
        win.rename_label_requested.connect(p.rename_label)
        win.delete_branch_requested.connect(p.delete_branch)
        win.rename_branch_requested.connect(p.rename_branch)
        win.shelve_requested.connect(p.shelve)
        win.unshelve_requested.connect(p.unshelve)
        win.refresh_shelves.connect(p.load_shelves)
        win.merge_branch_requested.connect(
            lambda name, preview, resolve, semantic: p.merge_branch(name, preview=preview, resolve=resolve, semantic=semantic)
        )
        win.undo_changeset_requested.connect(p.undo_changeset)
        win.undo_all_requested.connect(p.undo_all)
        win.undo_keep_requested.connect(p.undo_keep)
        win.rollback_cs_requested.connect(p.rollback_changeset)
        win.lock_requested.connect(lambda items: [p.lock_file(i) for i in items])
        win.unlock_requested.connect(lambda items: [p.unlock_file(i) for i in items])
        win.history_requested.connect(p.file_history)
        win.blame_requested.connect(p.blame_file)
        win.refresh_reviews.connect(p.load_reviews)
        win.create_review_requested.connect(p.create_review)
        win.edit_review_requested.connect(p.edit_review_status)
        win.delete_review_requested.connect(p.delete_review)
        win.load_changelist_status_requested.connect(p.load_changelist_status)
        win.move_to_changelist_requested.connect(p.move_to_changelist)

        # File ops (4.7)
        win.add_to_vcs_requested.connect(p.add_to_vcs)
        win.remove_from_vcs_requested.connect(p.remove_from_vcs)
        win.move_file_requested.connect(p.move_file)

        # Advanced diff (4.8)
        win.diff_cs_range_requested.connect(p.diff_cs_range)
        win.diff_branch_requested.connect(p.diff_branch)
        win.diff_labels_requested.connect(p.diff_labels)
        win.diff_shelve_requested.connect(p.diff_shelve)

        # CS edit comment (4.10)
        win.edit_cs_comment_requested.connect(p.edit_cs_comment)

        # Find (4.11)
        win.find_files_requested.connect(p.find_files)

        # Xlinks (5.4)
        win.refresh_xlinks.connect(p.load_xlinks)
        win.add_xlink_requested.connect(p.add_xlink)
        win.remove_xlink_requested.connect(p.remove_xlink)

        # Replication (5.5)
        win.push_replication_requested.connect(p.push_replication)
        win.pull_replication_requested.connect(p.pull_replication)
        win.replica_pkg_create_requested.connect(p.replica_package_create)
        win.replica_pkg_import_requested.connect(p.replica_package_import)

        # Attributes (5.6)
        win.load_attributes_requested.connect(p.load_attributes)
        win.set_attribute_requested.connect(p.set_attribute)
        win.delete_attribute_requested.connect(p.delete_attribute)

        # ACL (5.7)
        win.load_acl_requested.connect(p.load_acl)
        win.set_acl_requested.connect(p.set_acl_entry)
        win.delete_acl_requested.connect(p.delete_acl_entry)

        # Users / Groups (5.8)
        win.load_users_requested.connect(p.load_users)
        win.add_user_requested.connect(p.add_user)
        win.delete_user_requested.connect(p.delete_user)
        win.load_groups_requested.connect(p.load_groups)
        win.add_group_requested.connect(p.add_group)
        win.delete_group_requested.connect(p.delete_group)
        win.add_group_member_requested.connect(p.add_group_member)

        # Branch DAG (5.1)
        win.refresh_dag.connect(p.load_dag)

        # Three-way merge viewer (5.2)
        win.merge_view_requested.connect(p.open_merge_viewer)

        # Preferences / cm config (#8)
        win.load_config_requested.connect(p.load_config)
        win.set_config_requested.connect(p.set_config_entry)

        # Partial workspaces (#5)
        win.load_partial_status_requested.connect(p.load_partial_status)
        win.configure_partial_requested.connect(p.configure_partial)
        win.add_partial_requested.connect(p.add_partial)
        win.remove_partial_requested.connect(p.remove_partial)

        # Workspaces & Repos (#1)
        win.refresh_workspaces.connect(p.load_workspaces)
        win.create_workspace_requested.connect(p.create_workspace)
        win.delete_workspace_requested.connect(p.delete_workspace)
        win.refresh_repos.connect(p.load_repos)
        win.create_repo_requested.connect(p.create_repo)
        win.delete_repo_requested.connect(p.delete_repo)

        # Triggers (#6)
        win.refresh_triggers.connect(p.load_triggers)
        win.create_trigger_requested.connect(
            lambda name, event, filter_, command: p.create_trigger(name, event, filter_, command)
        )
        win.delete_trigger_requested.connect(p.delete_trigger)

        # Git Sync (#4)
        win.sync_git_requested.connect(p.sync_git)
        win.refresh_git_sync.connect(p.load_git_sync_status)

        # Hook up poll: Window's 100ms timer calls presenter.poll() (non-blocking)
        win._timer.timeout.connect(p.poll)  # type: ignore[attr-defined]

        win.destroyed.connect(lambda: (p.shutdown(), self._windows.pop(root, None)))
        self._windows[root] = (win, p)
        win.show()
        p.refresh()
