"""Unit tests for PanePresenter auto-trigger of dir size calc (Item #45)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from unittest import mock


from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.pane_presenter import PanePresenter


@dataclass
class StubView:
    items: list = field(default_factory=list)
    path: Path | None = None
    errors: list = field(default_factory=list)
    status: str = ""
    marked: set = field(default_factory=set)
    selected: str | None = None
    nav_history: list = field(default_factory=list)

    def set_items(self, items, **kwargs): self.items = list(items)
    def set_path(self, path): self.path = path
    def show_error(self, msg): self.errors.append(msg)
    def set_status(self, text): self.status = text
    def set_marked(self, paths): self.marked = set(paths)
    def current_cursor_item(self): return None
    def advance_cursor(self): pass
    def retreat_cursor(self): pass
    def set_filter_visible(self, v): pass
    def set_nav_history(self, paths): self.nav_history = list(paths)
    def select_item(self, name): self.selected = name
    def set_dir_size(self, path, size): pass


def test_auto_dir_sizes_called_on_navigate(tmp_path):
    (tmp_path / "sub").mkdir()
    view = StubView()
    presenter = PanePresenter(view, LocalVFS())
    with mock.patch.object(presenter, "calculate_all_dir_sizes") as m:
        presenter.navigate_to(tmp_path)
        presenter._nav_future.result()  # wait for pool job
        presenter.drain_nav()           # drain triggers calculate_all_dir_sizes
    m.assert_called_once()


def test_no_auto_dir_sizes_for_virtual(tmp_path):
    (tmp_path / "sub").mkdir()
    view = StubView()
    presenter = PanePresenter(view, LocalVFS())
    presenter.navigate_to(tmp_path)
    with mock.patch.object(presenter, "calculate_all_dir_sizes") as m:
        presenter.navigate_virtual([])
    m.assert_not_called()
