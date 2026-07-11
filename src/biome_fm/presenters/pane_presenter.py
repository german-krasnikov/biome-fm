"""PanePresenter — Qt-free directory navigation logic."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol


class PaneViewProtocol(Protocol):
    def set_items(self, items: list[FileItem]) -> None: ...
    def set_path(self, path: Path) -> None: ...
    def show_error(self, message: str) -> None: ...
    def set_status(self, text: str) -> None: ...


def _sort(items: list[FileItem]) -> list[FileItem]:
    # ponytail: sort here for unit testability; DirSortFilterProxy also sorts for
    # column-click UX — unify if they drift
    dirs = sorted((i for i in items if i.is_dir), key=lambda i: i.name.lower())
    files = sorted((i for i in items if not i.is_dir), key=lambda i: i.name.lower())
    return dirs + files


class PanePresenter:
    def __init__(
        self,
        view: PaneViewProtocol,
        vfs: VFSProtocol,
        home: Path | None = None,
    ) -> None:
        self._view = view
        self._vfs = vfs
        self._home = home or Path.home()
        self._cwd: Path | None = None
        self._back: list[Path] = []
        self._forward: list[Path] = []

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def current_path(self) -> Path:
        if self._cwd is None:
            raise RuntimeError("navigate_to() not called yet")
        return self._cwd

    @property
    def can_go_back(self) -> bool:
        return bool(self._back)

    @property
    def can_go_forward(self) -> bool:
        return bool(self._forward)

    def navigate_to(self, path: Path) -> None:
        old = self._cwd
        if self._navigate_no_history(path):
            if old is not None:
                self._back.append(old)
            self._forward.clear()

    def go_up(self) -> None:
        if self._cwd is None:
            return
        parent = self._cwd.parent
        if parent != self._cwd:
            self.navigate_to(parent)

    def go_home(self) -> None:
        self.navigate_to(self._home)

    def go_root(self) -> None:
        if self._cwd is None:
            return
        self.navigate_to(Path(self._cwd.anchor))

    def refresh(self) -> None:
        if self._cwd is not None:
            self._navigate_no_history(self._cwd)

    def go_back(self) -> None:
        if not self._back:
            return
        if self._cwd is not None:
            self._forward.append(self._cwd)
        self._navigate_no_history(self._back.pop())

    def go_forward(self) -> None:
        if not self._forward:
            return
        if self._cwd is not None:
            self._back.append(self._cwd)
        self._navigate_no_history(self._forward.pop())

    def on_item_activated(self, item: FileItem) -> None:
        if item.name == "..":
            self.go_up()
        elif item.is_dir:
            self.navigate_to(item.path)

    # ── internal ──────────────────────────────────────────────────────────────

    def _navigate_no_history(self, path: Path) -> bool:
        try:
            raw = self._vfs.listdir(path)
        except OSError as e:
            self._view.show_error(str(e))
            return False
        items = _sort(raw)
        if path.parent != path:
            dotdot = FileItem(name="..", path=path.parent, is_dir=True, size=0, modified=0.0)
            items = [dotdot, *items]
        self._cwd = path
        self._view.set_path(path)
        self._view.set_items(items)
        self._view.set_status(f"{len(raw)} items")
        return True
