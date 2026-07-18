"""ManagerPresenter — orchestrates both panes, commands, undo/redo. No Qt."""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from biome_fm.commands.base import Command, CommandHistory
from biome_fm.commands.copy_cmd import CopyCmd, ProgressCopyCmd
from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.commands.mkdir_cmd import MkdirCmd
from biome_fm.commands.move_cmd import MoveCmd, ProgressMoveCmd
from biome_fm.commands.rename_cmd import RenameCmd
from biome_fm.config import Config
from biome_fm.event_bus import (
    ActivePaneChanged,
    AsyncOpSubmitted,
    EventBus,
    OperationFinished,
    OperationStarted,
    ShowHiddenToggled,
    SyncBrowsingToggled,
)
from biome_fm.models.conflict_resolver import ConflictResolver
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol
from biome_fm.operations.task import OpConflict, OpProgress
from biome_fm.presenters.pane_presenter import PanePresenter

if TYPE_CHECKING:
    from biome_fm.operations.queue import OpQueue
    from biome_fm.plugins.manager import PluginManager

PaneId = Literal["left", "right"]
_OTHER: dict[PaneId, PaneId] = {"left": "right", "right": "left"}


@dataclass
class _OpSpec:
    """Op metadata for plugin hook calls."""
    op: str  # "copy" | "move" | "delete" | "mkdir" | "rename"
    src: Path | None = None
    dst: Path | None = None
    sources: list[Path] = field(default_factory=list)  # multi-source ops (copy/move/delete)


@dataclass
class ConfirmSpec:
    op: str  # "copy" | "move" | "delete"
    sources: list[Path]
    dest: Path | None = None


class ManagerPresenter:
    """Orchestrates both panes, file commands, and undo/redo. No Qt."""

    def __init__(
        self,
        left: PanePresenter,
        right: PanePresenter,
        vfs: VFSProtocol,
        history: CommandHistory | None = None,
        bus: EventBus | None = None,
        config: Config | None = None,
        op_queue: OpQueue | None = None,
        confirm: Callable[[ConfirmSpec], bool] | None = None,
        plugins: PluginManager | None = None,
    ) -> None:
        self._panes: dict[PaneId, PanePresenter] = {"left": left, "right": right}
        self._active: PaneId = "left"
        self._vfs = vfs
        self._history = history or CommandHistory()
        self._bus = bus
        self._config = config
        self._op_queue = op_queue
        self._confirm = confirm or (lambda _: True)
        self._plugins = plugins
        self._mirror = False
        self._mirroring = False
        self._pending_cmds: dict[int, Command] = {}
        self._pending_specs: dict[int, _OpSpec] = {}

    @property
    def active_pane_id(self) -> PaneId:
        return self._active

    @property
    def inactive_pane(self) -> PanePresenter:
        return self._panes[_OTHER[self._active]]

    @property
    def can_undo(self) -> bool:
        return self._history.can_undo

    @property
    def can_redo(self) -> bool:
        return self._history.can_redo

    @property
    def mirror(self) -> bool:
        return self._mirror

    def set_active_pane(self, pane_id: PaneId) -> None:
        if pane_id == self._active:
            return
        self._active = pane_id
        self._publish(ActivePaneChanged(pane_id))

    def switch_active_pane(self) -> None:
        self.set_active_pane(_OTHER[self._active])

    def swap_panes(self) -> None:
        left_path = self._panes["left"].current_path
        right_path = self._panes["right"].current_path
        self._panes["left"].navigate_to(right_path)
        self._panes["right"].navigate_to(left_path)

    def target_equals_source(self) -> None:
        self._target().navigate_to(self._source().current_path)

    def toggle_mirror(self) -> None:
        self._mirror = not self._mirror
        self._publish(SyncBrowsingToggled(self._mirror))

    def toggle_hidden(self) -> None:
        current = self._config.show_hidden if self._config else False
        enabled = not current
        if self._config:
            self._config.show_hidden = enabled
        self._publish(ShowHiddenToggled(enabled))

    def navigate_active(self, path: Path) -> None:
        if self._mirroring:
            return
        self._mirroring = True
        try:
            self._source().navigate_to(path)
            if self._mirror:
                self._target().navigate_to(path)
        finally:
            self._mirroring = False

    def copy_selected(self, items: list[FileItem]) -> None:
        if not items:
            return
        dst = self._target().current_path
        self._start_op([i.path for i in items], dst, move=False)

    def move_selected(self, items: list[FileItem]) -> None:
        if not items:
            return
        dst = self._target().current_path
        self._start_op([i.path for i in items], dst, move=True)

    def delete_selected(self, items: list[FileItem]) -> None:
        if not items:
            return
        paths = [i.path for i in items]
        if not self._confirm(ConfirmSpec("delete", paths)):
            return
        self._run(DeleteCmd(paths, self._vfs), "Delete", _OpSpec("delete", paths[0], sources=paths))

    def mkdir(self, name: str) -> None:
        path = self._source().current_path / name
        self._run(MkdirCmd(path, self._vfs), f"mkdir {name}", _OpSpec("mkdir", dst=path))

    def rename(self, item: FileItem, new_name: str) -> None:
        new_path = item.path.parent / new_name
        self._run(
            RenameCmd(item.path, new_name, self._vfs),
            f"Rename -> {new_name}",
            _OpSpec("rename", item.path, new_path),
        )

    def drop_files(
        self,
        paths: list[Path],
        target_pane_id: str,
        move: bool,
        target_folder: Path | None = None,
    ) -> None:
        if not paths:
            return
        dst = target_folder or self._panes[target_pane_id].current_path  # type: ignore[index]
        _dst = dst.resolve()
        sources = [
            rp for p in paths
            if (rp := p.resolve()).exists()
            and rp.parent != _dst
            and not _dst.is_relative_to(rp)
        ]
        if not sources:
            return
        self._start_op(sources, dst, move=move)

    def pop_pending_cmd(self, task_id: int) -> Command | None:
        return self._pending_cmds.pop(task_id, None)

    def fire_op_done(self, task_id: int) -> None:
        """Fire on_file_operation hook for each source of a completed async op."""
        spec = self._pending_specs.pop(task_id, None)
        if spec and self._plugins:
            for src in spec.sources if spec.sources else [spec.src]:
                self._plugins.hook.on_file_operation(op=spec.op, src=src, dst=spec.dst)

    def undo(self) -> None:
        self._history.undo()
        self._refresh_both()

    def redo(self) -> None:
        self._history.redo()
        self._refresh_both()

    def _start_op(self, sources: list[Path], dst: Path, move: bool) -> None:
        op = "move" if move else "copy"
        if not self._confirm(ConfirmSpec(op, sources, dst)):
            return
        if self._plugins:
            for src in sources:
                if self._plugins.hook.before_file_operation(op=op, src=src, dst=dst) is False:
                    return  # vetoed
        desc = "Move" if move else "Copy"
        if self._op_queue is None:
            cmd_cls = MoveCmd if move else CopyCmd
            self._run(cmd_cls(sources, dst, self._vfs), desc, _OpSpec(op, dst=dst, sources=sources))
            return
        cancel = threading.Event()
        task_id = self._op_queue.next_task_id()
        self._pending_specs[task_id] = _OpSpec(op, dst=dst, sources=sources)

        resolver = ConflictResolver()

        def _progress(
            files_done: int, files_total: int,
            bytes_done: int, bytes_total: int,
            current_file: str,
        ) -> None:
            self._op_queue.put_event(
                OpProgress(task_id, files_done, files_total, bytes_done, bytes_total, current_file)
            )

        def _on_conflict(src: object, dst_path: object, res: ConflictResolver) -> None:
            self._op_queue.put_event(OpConflict(task_id, src, dst_path, res))

        resolver.on_conflict = _on_conflict

        if move:
            cmd: Command = ProgressMoveCmd(sources, dst, self._vfs, cancel, _progress,
                                           conflict_resolver=resolver)
        else:
            cmd = ProgressCopyCmd(sources, dst, self._vfs, cancel, _progress,
                                  conflict_resolver=resolver)

        self._pending_cmds[task_id] = cmd
        self._op_queue.submit(cmd, cancel=cancel, task_id=task_id)
        self._publish(AsyncOpSubmitted(task_id, desc, cancel))

    def _source(self) -> PanePresenter:
        return self._panes[self._active]

    def _target(self) -> PanePresenter:
        return self._panes[_OTHER[self._active]]

    def _refresh_both(self) -> None:
        for p in self._panes.values():
            p.refresh()

    def _publish(self, event: object) -> None:
        if self._bus is not None:
            self._bus.publish(event)

    def move_tab_to_other_pane(self, pane_idx: int, tab_idx: int) -> None:
        """Move tab from one pane to the other. No-op if pane has only 1 tab."""
        pane_id: PaneId = "left" if pane_idx == 0 else "right"
        src = self._panes[pane_id]
        dst = self._panes[_OTHER[pane_id]]
        if not (hasattr(src, "tab_count") and hasattr(src, "presenter_at") and hasattr(src, "close_tab")):
            return
        if src.tab_count <= 1:  # type: ignore[attr-defined]
            return
        path = src.presenter_at(tab_idx).current_path  # type: ignore[attr-defined]
        dst.new_tab(path)  # type: ignore[attr-defined]
        src.close_tab(tab_idx)  # type: ignore[attr-defined]

    def multi_rename(self, renames: list[tuple[Path, str]]) -> None:
        """Execute batch rename. renames = [(old_path, new_name), ...]"""
        if not renames:
            return
        from biome_fm.commands.multi_rename_cmd import MultiRenameCmd
        pairs = [(p, p.parent / n) for p, n in renames]
        self._run(MultiRenameCmd(pairs, self._vfs), f"Rename {len(renames)} item(s)")

    def compress(self, items: list[FileItem], archive_path: Path) -> None:
        from biome_fm.commands.archive_cmd import ArchiveCmd
        sources = [i.path for i in items]
        self._run(
            ArchiveCmd(sources, archive_path),
            "Compress",
            _OpSpec("compress", dst=archive_path, sources=sources),
        )

    def extract(self, item: FileItem) -> None:
        from biome_fm.commands.archive_cmd import ExtractCmd
        dst = self._source().current_path
        self._run(
            ExtractCmd(item.path, dst),
            "Extract",
            _OpSpec("extract", src=item.path, dst=dst),
        )

    def _run(self, cmd: Command, desc: str, spec: _OpSpec | None = None) -> None:
        if self._plugins and spec and spec.src:
            if self._plugins.hook.before_file_operation(op=spec.op, src=spec.src, dst=spec.dst) is False:
                return  # vetoed
        self._publish(OperationStarted(desc))
        try:
            self._history.execute(cmd)
            self._refresh_both()
            self._publish(OperationFinished(desc, True))
            if self._plugins and spec:
                for src in spec.sources if spec.sources else [spec.src]:
                    self._plugins.hook.on_file_operation(op=spec.op, src=src, dst=spec.dst)
        except OSError as e:
            self._publish(OperationFinished(desc, False, str(e)))
            raise
