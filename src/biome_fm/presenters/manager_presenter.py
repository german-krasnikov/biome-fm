"""ManagerPresenter — orchestrates both panes, commands, undo/redo. No Qt."""
from __future__ import annotations

import threading
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
)
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol
from biome_fm.presenters.pane_presenter import PanePresenter

if TYPE_CHECKING:
    from biome_fm.operations.queue import OpQueue

PaneId = Literal["left", "right"]
_OTHER: dict[PaneId, PaneId] = {"left": "right", "right": "left"}


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
    ) -> None:
        self._panes: dict[PaneId, PanePresenter] = {"left": left, "right": right}
        self._active: PaneId = "left"
        self._vfs = vfs
        self._history = history or CommandHistory()
        self._bus = bus
        self._config = config
        self._op_queue = op_queue
        self._mirror = False
        self._mirroring = False
        self._pending_cmds: dict[int, Command] = {}

    @property
    def active_pane_id(self) -> PaneId:
        return self._active

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

    def toggle_mirror(self) -> None:
        self._mirror = not self._mirror

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
        self._run(DeleteCmd([i.path for i in items], self._vfs), "Delete")

    def mkdir(self, name: str) -> None:
        path = self._source().current_path / name
        self._run(MkdirCmd(path, self._vfs), f"mkdir {name}")

    def rename(self, item: FileItem, new_name: str) -> None:
        self._run(RenameCmd(item.path, new_name, self._vfs), f"Rename -> {new_name}")

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
        sources = [
            p.resolve() for p in paths
            if p.resolve().exists() and p.parent.resolve() != dst.resolve()
        ]
        if not sources:
            return
        self._start_op(sources, dst, move=move)

    def pop_pending_cmd(self, task_id: int) -> Command | None:
        return self._pending_cmds.pop(task_id, None)

    def undo(self) -> None:
        self._history.undo()
        self._refresh_both()

    def redo(self) -> None:
        self._history.redo()
        self._refresh_both()

    def _start_op(self, sources: list[Path], dst: Path, move: bool) -> None:
        desc = "Move" if move else "Copy"
        if self._op_queue is None:
            cmd_cls = MoveCmd if move else CopyCmd
            self._run(cmd_cls(sources, dst, self._vfs), desc)
            return
        cancel = threading.Event()
        task_id = self._op_queue.next_task_id()

        def _noop(*_args: object) -> None:
            pass  # progress events are pushed via OpProgress by ProgressCopyCmd itself

        if move:
            cmd: Command = ProgressMoveCmd(sources, dst, self._vfs, cancel, _noop)
        else:
            cmd = ProgressCopyCmd(sources, dst, self._vfs, cancel, _noop)

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

    def _run(self, cmd: Command, desc: str) -> None:
        self._publish(OperationStarted(desc))
        try:
            self._history.execute(cmd)
            self._refresh_both()
            self._publish(OperationFinished(desc, True))
        except OSError as e:
            self._publish(OperationFinished(desc, False, str(e)))
            raise
