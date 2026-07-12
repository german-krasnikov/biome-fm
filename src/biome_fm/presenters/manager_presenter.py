"""ManagerPresenter — orchestrates both panes, commands, undo/redo. No Qt."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from biome_fm.commands.base import Command, CommandHistory
from biome_fm.commands.copy_cmd import CopyCmd
from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.commands.mkdir_cmd import MkdirCmd
from biome_fm.commands.move_cmd import MoveCmd
from biome_fm.commands.rename_cmd import RenameCmd
from biome_fm.event_bus import (
    ActivePaneChanged,
    EventBus,
    OperationFinished,
    OperationStarted,
)
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol
from biome_fm.presenters.pane_presenter import PanePresenter

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
    ) -> None:
        self._panes: dict[PaneId, PanePresenter] = {"left": left, "right": right}
        self._active: PaneId = "left"
        self._vfs = vfs
        self._history = history or CommandHistory()
        self._bus = bus
        self._mirror = False
        self._mirroring = False

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
        self._run(CopyCmd([i.path for i in items], dst, self._vfs), "Copy")

    def move_selected(self, items: list[FileItem]) -> None:
        if not items:
            return
        dst = self._target().current_path
        self._run(MoveCmd([i.path for i in items], dst, self._vfs), "Move")

    def delete_selected(self, items: list[FileItem]) -> None:
        if not items:
            return
        self._run(DeleteCmd([i.path for i in items], self._vfs), "Delete")

    def mkdir(self, name: str) -> None:
        path = self._source().current_path / name
        self._run(MkdirCmd(path, self._vfs), f"mkdir {name}")

    def rename(self, item: FileItem, new_name: str) -> None:
        self._run(RenameCmd(item.path, new_name, self._vfs), f"Rename -> {new_name}")

    def drop_files(self, paths: list[Path], target_pane_id: str, move: bool) -> None:
        if not paths:
            return
        dst = self._panes[target_pane_id].current_path  # type: ignore[index]
        sources = [p.resolve() for p in paths if p.exists() and p.parent.resolve() != dst.resolve()]
        if not sources:
            return
        cmd_cls = MoveCmd if move else CopyCmd
        self._run(cmd_cls(sources, dst, self._vfs), "Move" if move else "Copy")

    def undo(self) -> None:
        self._history.undo()
        self._refresh_both()

    def redo(self) -> None:
        self._history.redo()
        self._refresh_both()

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
