"""F287 — Smart Group Select (Same Extension / Size / Date)."""
import datetime
from dataclasses import dataclass, field
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter

BASE = Path("/home/user")


@dataclass
class _FakeView:
    items: list = field(default_factory=list)
    path: Path | None = None
    errors: list = field(default_factory=list)
    status: str = ""
    marked: set = field(default_factory=set)
    cursor: FileItem | None = None
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


class _FakeVFS:
    def __init__(self, items): self._items = items
    def listdir(self, path): return list(self._items)


def _item(name, size=100, mtime=1_000_000.0):
    return FileItem(name=name, path=BASE / name, is_dir=False, size=size, modified=mtime)


def _setup(items):
    view = _FakeView()
    vfs = _FakeVFS(items)
    p = PanePresenter(view=view, vfs=vfs, home=BASE)
    p.navigate_to(BASE)
    return p, view


def test_select_same_ext():
    items = [_item("a.py"), _item("b.py"), _item("c.txt")]
    p, view = _setup(items)
    view.cursor = next(i for i in p._items if i.name == "a.py")
    p.select_same_ext()
    names = {Path(s).name for s in p._marks}
    assert "a.py" in names
    assert "b.py" in names
    assert "c.txt" not in names


def test_select_same_size_group():
    items = [_item("a.bin", size=100), _item("b.bin", size=105), _item("c.bin", size=200)]
    p, view = _setup(items)
    view.cursor = next(i for i in p._items if i.name == "a.bin")
    p.select_same_size_group()
    names = {Path(s).name for s in p._marks}
    assert "a.bin" in names
    assert "b.bin" in names   # 105 within ±10% of 100
    assert "c.bin" not in names  # 200 not within ±10% of 100


def test_select_same_date():
    ts = datetime.datetime(2024, 3, 15, 10, 0, 0).timestamp()
    ts2 = datetime.datetime(2024, 3, 15, 22, 0, 0).timestamp()
    ts_other = datetime.datetime(2024, 3, 16, 10, 0, 0).timestamp()
    items = [_item("a.txt", mtime=ts), _item("b.txt", mtime=ts2), _item("c.txt", mtime=ts_other)]
    p, view = _setup(items)
    view.cursor = next(i for i in p._items if i.name == "a.txt")
    p.select_same_date()
    names = {Path(s).name for s in p._marks}
    assert "a.txt" in names
    assert "b.txt" in names   # same day
    assert "c.txt" not in names  # different day
