"""TabsPresenter — manages multiple PanePresenter tabs. No Qt."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol
from biome_fm.presenters.pane_presenter import PanePresenter, PaneViewProtocol


class TabsViewProtocol(Protocol):
    def add_tab(self, title: str) -> int: ...
    def remove_tab(self, idx: int) -> None: ...
    def set_active_tab(self, idx: int) -> None: ...
    def set_tab_title(self, idx: int, title: str) -> None: ...


class TabsPresenter:
    """Manages N PanePresenter tabs. Duck-types as PanePresenter for ManagerPresenter."""

    def __init__(
        self,
        vfs: VFSProtocol,
        tabs_view: TabsViewProtocol,
        view_factory: Callable[[], PaneViewProtocol],
    ) -> None:
        self._vfs = vfs
        self._tabs_view = tabs_view
        self._view_factory = view_factory
        self._tabs: list[PanePresenter] = []
        self._views: list[PaneViewProtocol] = []
        self._active_idx: int = 0

    # ── tab management ────────────────────────────────────────────────────────

    @property
    def active(self) -> PanePresenter:
        if not self._tabs:
            raise RuntimeError("TabsPresenter has no tabs — call new_tab() first")
        return self._tabs[self._active_idx]

    @property
    def active_idx(self) -> int:
        return self._active_idx

    @property
    def tab_count(self) -> int:
        return len(self._tabs)

    def new_tab(self, path: Path) -> PanePresenter:
        view = self._view_factory()
        presenter = PanePresenter(view=view, vfs=self._vfs)
        self._tabs.append(presenter)
        self._views.append(view)
        idx = self._tabs_view.add_tab(path.name or str(path))
        self._active_idx = idx
        self._tabs_view.set_active_tab(idx)
        presenter.navigate_to(path)
        return presenter

    def close_tab(self, idx: int) -> None:
        if self.tab_count <= 1:
            return
        self._tabs.pop(idx)
        self._views.pop(idx)
        self._tabs_view.remove_tab(idx)
        if self._active_idx >= self.tab_count:
            self._active_idx = self.tab_count - 1
        elif self._active_idx > idx:
            self._active_idx -= 1
        self._tabs_view.set_active_tab(self._active_idx)

    def switch_tab(self, idx: int) -> None:
        if 0 <= idx < self.tab_count:
            self._active_idx = idx
            self._tabs_view.set_active_tab(idx)

    def paths(self) -> list[Path]:
        return [t.current_path for t in self._tabs]

    def view_at(self, idx: int) -> PaneViewProtocol:
        return self._views[idx]

    # ── PanePresenter delegation for ManagerPresenter ─────────────────────────

    @property
    def current_path(self) -> Path:
        return self.active.current_path

    @property
    def can_go_back(self) -> bool:
        return self.active.can_go_back

    @property
    def can_go_forward(self) -> bool:
        return self.active.can_go_forward

    @property
    def marks(self) -> set[Path]:
        return self.active.marks

    @property
    def marked_items(self) -> list[FileItem]:
        return self.active.marked_items

    def navigate_to(self, path: Path) -> None:
        self.active.navigate_to(path)
        self._tabs_view.set_tab_title(self._active_idx, path.name or str(path))

    def refresh(self) -> None:
        self.active.refresh()

    def go_back(self) -> None:
        self.active.go_back()

    def go_forward(self) -> None:
        self.active.go_forward()

    def go_up(self) -> None:
        self.active.go_up()

    def go_home(self) -> None:
        self.active.go_home()

    def toggle_mark(self) -> None:
        self.active.toggle_mark()

    def select_all(self) -> None:
        self.active.select_all()

    def deselect_all(self) -> None:
        self.active.deselect_all()

    def invert_selection(self) -> None:
        self.active.invert_selection()

    def select_by_pattern(self, pattern: str) -> None:
        self.active.select_by_pattern(pattern)

    def deselect_by_pattern(self, pattern: str) -> None:
        self.active.deselect_by_pattern(pattern)

    def current_item(self) -> FileItem | None:
        return self.active.current_item()

    def on_item_activated(self, item: FileItem) -> None:
        self.active.on_item_activated(item)
