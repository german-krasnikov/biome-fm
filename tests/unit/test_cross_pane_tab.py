"""TDD: cross-pane tab move in ManagerPresenter."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.tabs_presenter import TabsPresenter
from biome_fm.presenters.pane_presenter import PanePresenter
from dataclasses import dataclass, field


# ── fakes ─────────────────────────────────────────────────────────────────────

@dataclass
class _FakeTabsView:
    tabs: list = field(default_factory=list)
    active: int = 0
    titles: dict = field(default_factory=dict)

    def add_tab(self, title: str) -> int:
        self.tabs.append(title)
        return len(self.tabs) - 1

    def remove_tab(self, idx: int) -> None:
        self.tabs.pop(idx)

    def set_active_tab(self, idx: int) -> None:
        self.active = idx

    def set_tab_title(self, idx: int, title: str) -> None:
        self.titles[idx] = title

    def set_tab_tooltip(self, idx: int, tooltip: str) -> None:
        pass


@dataclass
class _FakePaneView:
    items: list = field(default_factory=list)
    path_text: str = ""

    def set_items(self, items, **kwargs): self.items = items
    def set_path(self, path): self.path_text = str(path)
    def set_status(self, t): pass
    def show_error(self, m): pass
    def set_marked(self, p): pass
    def current_cursor_item(self): return None
    def advance_cursor(self): pass
    def retreat_cursor(self): pass
    def set_filter_visible(self, v): pass
    def set_nav_history(self, p): pass
    def select_item(self, n): pass


def _make_tabs(vfs, tmp_path: Path) -> tuple[TabsPresenter, _FakeTabsView]:
    tv = _FakeTabsView()
    tp = TabsPresenter(vfs, tv, _FakePaneView)
    tp.new_tab(tmp_path)
    return tp, tv


# ── tests ─────────────────────────────────────────────────────────────────────

def test_tab_moves_to_other_pane(tmp_path: Path) -> None:
    vfs = LocalVFS()
    src_dir = tmp_path / "src"; src_dir.mkdir()
    extra_dir = tmp_path / "extra"; extra_dir.mkdir()

    left, _ = _make_tabs(vfs, src_dir)
    right, _ = _make_tabs(vfs, tmp_path)

    # add a second tab so source has 2 tabs
    left.new_tab(extra_dir)
    assert left.tab_count == 2

    mgr = ManagerPresenter(left, right, vfs)
    mgr.move_tab_to_other_pane(pane_idx=0, tab_idx=1)

    # extra_dir should now be a tab in right pane
    assert any(p == extra_dir for p in right.paths())
    # left should have one less tab
    assert left.tab_count == 1


def test_last_tab_not_moved(tmp_path: Path) -> None:
    vfs = LocalVFS()
    left, _ = _make_tabs(vfs, tmp_path)
    right, _ = _make_tabs(vfs, tmp_path)

    assert left.tab_count == 1
    mgr = ManagerPresenter(left, right, vfs)
    mgr.move_tab_to_other_pane(pane_idx=0, tab_idx=0)

    # nothing changed — can't remove last tab
    assert left.tab_count == 1
