"""PanePresenter — Qt-free directory navigation logic."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Protocol

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol


class PaneViewProtocol(Protocol):
    def set_items(self, items: list[FileItem]) -> None: ...
    def set_path(self, path: Path) -> None: ...
    def show_error(self, message: str) -> None: ...
    def set_status(self, text: str) -> None: ...
    def set_marked(self, paths: set[Path]) -> None: ...
    def current_cursor_item(self) -> FileItem | None: ...
    def advance_cursor(self) -> None: ...


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
        self._items: list[FileItem] = []
        self._marks: set[Path] = set()

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

    @property
    def marks(self) -> set[Path]:
        return set(self._marks)

    @property
    def marked_items(self) -> list[FileItem]:
        return [i for i in self._items if i.path in self._marks]

    def current_item(self) -> FileItem | None:
        return self._view.current_cursor_item()

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

    def toggle_mark(self) -> None:
        """Mark cursor item + advance cursor (TC Space behavior)."""
        item = self._view.current_cursor_item()
        if item is None or item.name == "..":
            return
        self._marks ^= {item.path}
        self._push_marks()
        self._view.advance_cursor()

    def select_all(self) -> None:
        self._marks = {i.path for i in self._items}
        self._push_marks()

    def deselect_all(self) -> None:
        self._marks.clear()
        self._push_marks()

    def invert_selection(self) -> None:
        self._marks = {i.path for i in self._items} - self._marks
        self._push_marks()

    def select_by_pattern(self, pattern: str) -> None:
        self._marks |= {i.path for i in self._items if fnmatch.fnmatch(i.name, pattern)}
        self._push_marks()

    def deselect_by_pattern(self, pattern: str) -> None:
        self._marks -= {i.path for i in self._items if fnmatch.fnmatch(i.name, pattern)}
        self._push_marks()

    # ── internal ──────────────────────────────────────────────────────────────

    def _push_marks(self) -> None:
        self._view.set_marked(set(self._marks))
        self._update_status()

    def _update_status(self) -> None:
        total = len(self._items)
        if self._marks:
            size = sum(i.size for i in self._items if i.path in self._marks and not i.is_dir)
            mark_str = f"{len(self._marks)} marked ({self._fmt_size(size)})"
            self._view.set_status(f"{total} items, {mark_str}")
        else:
            self._view.set_status(f"{total} items")

    @staticmethod
    def _fmt_size(n: int) -> str:
        s = float(n)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if s < 1024:
                return f"{s:.0f} {unit}" if unit == "B" else f"{s:.1f} {unit}"
            s /= 1024
        return f"{s:.1f} PB"

    def _navigate_no_history(self, path: Path) -> bool:
        try:
            raw = self._vfs.listdir(path)
        except OSError as e:
            self._view.show_error(str(e))
            return False
        if path != self._cwd:
            self._marks.clear()
        self._items = _sort(raw)
        items = list(self._items)
        if path.parent != path:
            dotdot = FileItem(name="..", path=path.parent, is_dir=True, size=0, modified=0.0)
            items = [dotdot, *items]
        self._cwd = path
        self._view.set_path(path)
        self._view.set_items(items)
        self._view.set_marked(set(self._marks))
        self._update_status()
        return True
