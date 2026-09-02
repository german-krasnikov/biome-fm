"""TabsPresenter — manages multiple PanePresenter tabs. No Qt."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from biome_fm.models.dir_state_store import DirStateStore
from biome_fm.models.file_item import FileItem
from biome_fm.models.frecency_store import FrecencyStore
from biome_fm.models.vfs import VFSProtocol
from biome_fm.presenters.pane_presenter import PanePresenter, PaneViewProtocol


class TabsViewProtocol(Protocol):
    def add_tab(self, title: str) -> int: ...
    def remove_tab(self, idx: int) -> None: ...
    def set_active_tab(self, idx: int) -> None: ...
    def set_tab_title(self, idx: int, title: str) -> None: ...
    def set_tab_tooltip(self, idx: int, tooltip: str) -> None: ...


class TabsPresenter:
    """Manages N PanePresenter tabs. Duck-types as PanePresenter for ManagerPresenter."""

    def __init__(
        self,
        vfs: VFSProtocol,
        tabs_view: TabsViewProtocol,
        view_factory: Callable[[], PaneViewProtocol],
        opener: Callable[[Path], None] | None = None,
        store: DirStateStore | None = None,
        frecency: FrecencyStore | None = None,
    ) -> None:
        self._vfs = vfs
        self._tabs_view = tabs_view
        self._view_factory = view_factory
        self._opener = opener
        self._store = store
        self._frecency = frecency
        self._tabs: list[PanePresenter] = []
        self._views: list[PaneViewProtocol] = []
        self._active_idx: int = 0
        self._locked: set[int] = set()
        self._links: dict[int, tuple[TabsPresenter, int]] = {}
        self._pending: dict[int, Path] = {}  # deferred tab paths
        self.on_tab_created: Callable[[PaneViewProtocol, PanePresenter], None] | None = None

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

    def new_tab(self, path: Path, deferred: bool = False) -> PanePresenter:
        view = self._view_factory()
        presenter = PanePresenter(view=view, vfs=self._vfs, opener=self._opener, store=self._store, frecency=self._frecency)
        self._tabs.append(presenter)
        self._views.append(view)
        idx = self._tabs_view.add_tab("")
        self._active_idx = idx
        self._tabs_view.set_active_tab(idx)
        if deferred:
            self._pending[idx] = path
        else:
            presenter.navigate_to(path)
        if self.on_tab_created is not None:
            self.on_tab_created(view, presenter)
        return presenter

    def lock_tab(self, idx: int) -> None:
        self._locked.add(idx)

    def unlock_tab(self, idx: int) -> None:
        self._locked.discard(idx)

    def is_locked(self, idx: int) -> bool:
        return idx in self._locked

    def link_tab(self, local_idx: int, other: TabsPresenter, other_idx: int) -> None:
        self._links[local_idx] = (other, other_idx)
        other._links[other_idx] = (self, local_idx)

    def unlink_tab(self, local_idx: int) -> None:
        if local_idx in self._links:
            other, other_idx = self._links.pop(local_idx)
            other._links.pop(other_idx, None)

    def is_linked(self, idx: int) -> bool:
        return idx in self._links

    def shutdown(self) -> None:
        """Cancel background work in all tab presenters. Call on window close."""
        for presenter in self._tabs:
            presenter.cleanup()

    def close_tab(self, idx: int) -> None:
        if self.tab_count <= 1 or idx in self._locked:
            return
        self._tabs[idx].cleanup()
        self._tabs.pop(idx)
        self._views.pop(idx)
        # Shift indices BEFORE remove_tab so Qt currentChanged fires with correct state
        self._locked = {k - 1 if k > idx else k for k in self._locked}
        self._pending = {(k - 1 if k > idx else k): v for k, v in self._pending.items() if k != idx}
        self._links = {(k - 1 if k > idx else k): v for k, v in self._links.items() if k != idx}
        for new_k, (other, other_k) in self._links.items():
            other._links[other_k] = (self, new_k)
        if self._active_idx >= self.tab_count:
            self._active_idx = self.tab_count - 1
        elif self._active_idx > idx:
            self._active_idx -= 1
        self._tabs_view.remove_tab(idx)
        self._tabs_view.set_active_tab(self._active_idx)
        # Eagerly load new active tab if it was deferred
        if self._active_idx in self._pending:
            self._tabs[self._active_idx].navigate_to(self._pending.pop(self._active_idx))

    def replace_all(self, paths: list[Path], active_idx: int) -> None:
        """Replace every tab with deferred tabs at *paths*; *active_idx* indexes *paths*."""
        old = self.tab_count if paths else 0
        for p in paths:
            self.new_tab(p, deferred=True)      # on_tab_created fires per tab
        self.switch_tab(active_idx + old)       # load target before old tabs go
        for i in range(old):
            self.unlock_tab(i)
            self.unlink_tab(i)
        for _ in range(old):
            self.close_tab(0)

    def duplicate_tab(self, idx: int) -> PanePresenter:
        """Open a new tab at the same path as tab[idx]."""
        return self.new_tab(self._safe_path(idx))

    def switch_tab(self, idx: int) -> None:
        if 0 <= idx < self.tab_count:
            self._active_idx = idx
            self._tabs_view.set_active_tab(idx)
            if idx in self._pending:
                self._tabs[idx].navigate_to(self._pending.pop(idx))

    def paths(self) -> list[Path]:
        return [self._safe_path(i) for i in range(len(self._tabs))]

    def _safe_path(self, idx: int) -> Path:
        """Return path for tab idx without raising for deferred/error tabs."""
        if idx in self._pending:
            return self._pending[idx]
        try:
            return self._tabs[idx].current_path
        except RuntimeError:
            return Path.home()

    def view_at(self, idx: int) -> PaneViewProtocol:
        return self._views[idx]

    def presenter_at(self, idx: int) -> PanePresenter:
        return self._tabs[idx]

    def save_group(self, name: str, store: object) -> None:
        store.save_group(name, self.paths())  # type: ignore[attr-defined]

    def load_group(self, name: str, store: object) -> None:
        for path in store.load_group(name):  # type: ignore[attr-defined]
            self.new_tab(path)

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
        if self._active_idx in self._locked:
            self.new_tab(path)
            return
        self.active.navigate_to(path)
        self._tabs_view.set_tab_title(self._active_idx, str(path))
        self._tabs_view.set_tab_tooltip(self._active_idx, str(path))
        if self._active_idx in self._links:
            other, other_idx = self._links[self._active_idx]
            other._tabs[other_idx].navigate_to(path)
            other._tabs_view.set_tab_title(other_idx, str(path))
            other._tabs_view.set_tab_tooltip(other_idx, str(path))

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

    def toggle_mark_up(self) -> None:
        self.active.toggle_mark_up()

    def toggle_mark_at(self, item: FileItem) -> None:
        self.active.toggle_mark_at(item)

    def go_root(self) -> None:
        self.active.go_root()

    def toggle_flat_view(self) -> None:
        self.active.toggle_flat_view()

    def navigate_virtual(self, items, label="Search Results", *, on_activate=None):
        self.active.navigate_virtual(items, label, on_activate=on_activate)

    def on_item_activated(self, item: FileItem) -> None:
        if item.is_dir and self._active_idx in self._locked:
            self.new_tab(item.path)
            return
        self.active.on_item_activated(item)
        p = self.active.current_path
        self._tabs_view.set_tab_title(self._active_idx, p.name or str(p))
        self._tabs_view.set_tab_tooltip(self._active_idx, str(p))
