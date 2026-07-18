"""F247 — Sort Modes Quick-Cycle."""
from dataclasses import dataclass, field
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


@dataclass
class _FakeView:
    items: list = field(default_factory=list)
    path: Path | None = None
    errors: list = field(default_factory=list)
    status: str = ""
    marked: set = field(default_factory=set)
    cursor: FileItem | None = None
    sort_calls: list = field(default_factory=list)
    nav_history: list = field(default_factory=list)

    def set_items(self, items, **kwargs): self.items = list(items)
    def set_path(self, path): self.path = path
    def show_error(self, msg): self.errors.append(msg)
    def set_status(self, text): self.status = text
    def set_marked(self, paths): self.marked = set(paths)
    def current_cursor_item(self): return self.cursor
    def advance_cursor(self): pass
    def retreat_cursor(self): pass
    def set_filter_visible(self, v): pass
    def set_nav_history(self, paths): self.nav_history = list(paths)
    def select_item(self, name): pass
    def set_dir_size(self, path, size): pass
    def set_sort_preset(self, col, asc): self.sort_calls.append((col, asc))


class _FakeVFS:
    def listdir(self, path): return []


def _make():
    view = _FakeView()
    p = PanePresenter(view=view, vfs=_FakeVFS(), home=Path("/home"))
    return p, view


def test_cycle_sort_advances():
    p, _ = _make()
    assert p._sort_preset == 0
    p.cycle_sort()
    assert p._sort_preset == 1
    p.cycle_sort()
    assert p._sort_preset == 2


def test_cycle_sort_wraps_around():
    p, _ = _make()
    for _ in range(len(p._SORT_PRESETS)):
        p.cycle_sort()
    assert p._sort_preset == 0


def test_cycle_sort_calls_view():
    p, view = _make()
    p.cycle_sort()
    assert len(view.sort_calls) == 1
    col, asc = view.sort_calls[0]
    assert isinstance(col, int)
    assert isinstance(asc, bool)
