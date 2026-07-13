"""Unit tests for PanePresenter — NO Qt dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _item(name: str, parent: Path, *, is_dir: bool = False, size: int = 0) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=size, modified=0.0)


class FakeVFS:
    """Dict-backed in-memory VFS."""

    def __init__(self, tree: dict[Path, list[FileItem]]) -> None:
        self._tree = tree
        self._denied: set[Path] = set()

    def listdir(self, path: Path) -> list[FileItem]:
        if path in self._denied:
            raise PermissionError(f"Permission denied: {path}")
        if path not in self._tree:
            raise FileNotFoundError(f"Not found: {path}")
        return list(self._tree[path])

    def exists(self, path: Path) -> bool:
        return path in self._tree or any(
            i.path == path for items in self._tree.values() for i in items
        )

    def deny(self, path: Path) -> None:
        self._denied.add(path)

    def copy(self, s: Path, d: Path) -> None: ...
    def move(self, s: Path, d: Path) -> None: ...
    def delete(self, p: Path) -> None: ...
    def mkdir(self, p: Path) -> None: ...
    def stat(self, p: Path) -> FileItem: ...  # type: ignore[return]


@dataclass
class FakePaneView:
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    errors: list[str] = field(default_factory=list)
    status: str = ""
    marked: set[Path] = field(default_factory=set)
    cursor: FileItem | None = None
    cursor_advances: int = 0
    cursor_retreats: int = 0
    nav_history: list[Path] = field(default_factory=list)
    selected: str | None = None

    def set_items(self, items: list[FileItem]) -> None:
        self.items = list(items)

    def set_path(self, path: Path) -> None:
        self.path = path

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def set_status(self, text: str) -> None:
        self.status = text

    def set_marked(self, paths: set[Path]) -> None:
        self.marked = set(paths)

    def current_cursor_item(self) -> FileItem | None:
        return self.cursor

    def advance_cursor(self) -> None:
        self.cursor_advances += 1

    def retreat_cursor(self) -> None:
        self.cursor_retreats += 1

    def set_filter_visible(self, visible: bool) -> None:
        pass

    def set_nav_history(self, paths: list[Path]) -> None:
        self.nav_history = list(paths)

    def select_item(self, name: str) -> None:
        self.selected = name


# ── fixtures ────────────────────────────────────────────────────────────────

ROOT = Path("/")
HOME = ROOT / "home"
DOCS = HOME / "docs"


def _make_tree() -> dict[Path, list[FileItem]]:
    return {
        ROOT: [_item("home", ROOT, is_dir=True)],
        HOME: [
            _item("docs", HOME, is_dir=True),
            _item("archive", HOME, is_dir=True),
            _item("readme.txt", HOME, size=100),
            _item("zebra.txt", HOME, size=50),
        ],
        DOCS: [_item("notes.md", DOCS, size=30)],
    }


@pytest.fixture
def env():
    tree = _make_tree()
    vfs = FakeVFS(tree)
    view = FakePaneView()
    from biome_fm.presenters.pane_presenter import PanePresenter
    p = PanePresenter(view=view, vfs=vfs, home=HOME)
    return p, view, vfs, tree


# ── tests ────────────────────────────────────────────────────────────────────

class TestNavigateTo:
    def test_navigate_to_sets_path_on_view(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        assert view.path == HOME

    def test_navigate_to_pushes_items_to_view(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        # ".." + 2 dirs + 2 files = 5
        assert len(view.items) == 5

    def test_navigate_to_sorts_dirs_first(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        # skip ".." at index 0
        real_items = [i for i in view.items if i.name != ".."]
        dirs = [i for i in real_items if i.is_dir]
        files = [i for i in real_items if not i.is_dir]
        # all dirs appear before first file
        dir_indices = [view.items.index(i) for i in dirs]
        file_indices = [view.items.index(i) for i in files]
        assert max(dir_indices) < min(file_indices)

    def test_navigate_to_sorts_alpha_within_groups(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        real = [i for i in view.items if i.name != ".."]
        dirs = [i for i in real if i.is_dir]
        files = [i for i in real if not i.is_dir]
        assert [d.name for d in dirs] == sorted(d.name for d in dirs)
        assert [f.name for f in files] == sorted(f.name for f in files)

    def test_navigate_to_nonexistent_shows_error(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)  # set initial path
        bad = ROOT / "nope"
        p.navigate_to(bad)
        assert len(view.errors) == 1
        assert view.path == HOME  # unchanged

    def test_navigate_to_permission_denied_shows_error(self, env):
        p, view, vfs, _ = env
        p.navigate_to(HOME)
        vfs.deny(DOCS)
        p.navigate_to(DOCS)
        assert len(view.errors) == 1
        assert view.path == HOME

    def test_navigate_to_prepends_dotdot(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        assert view.items[0].name == ".."

    def test_navigate_to_root_no_dotdot(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(ROOT)
        names = [i.name for i in view.items]
        assert ".." not in names

    def test_current_path_property(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(HOME)
        assert p.current_path == HOME
        p.navigate_to(DOCS)
        assert p.current_path == DOCS


class TestNavigation:
    def test_go_up_from_subdir(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(DOCS)
        p.go_up()
        assert p.current_path == HOME

    def test_go_up_at_root_is_noop(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(ROOT)
        p.go_up()
        assert p.current_path == ROOT

    def test_go_home(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(DOCS)
        p.go_home()
        assert p.current_path == HOME

    def test_go_root(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(HOME)
        p.go_root()
        assert p.current_path == ROOT

    def test_refresh_reloads(self, env):
        p, view, _vfs, tree = env
        p.navigate_to(HOME)
        new_item = _item("new_file.txt", HOME, size=1)
        tree[HOME].append(new_item)
        p.refresh()
        names = [i.name for i in view.items]
        assert "new_file.txt" in names


class TestActivate:
    def test_activate_dir_navigates(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(HOME)
        docs_item = _item("docs", HOME, is_dir=True)
        p.on_item_activated(docs_item)
        assert p.current_path == DOCS

    def test_activate_file_no_navigation(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        file_item = _item("readme.txt", HOME, size=100)
        p.on_item_activated(file_item)
        assert p.current_path == HOME
        assert not view.errors

    def test_activate_dotdot_goes_up(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(DOCS)
        dotdot = FileItem(name="..", path=HOME, is_dir=True, size=0, modified=0.0)
        p.on_item_activated(dotdot)
        assert p.current_path == HOME


class TestHistory:
    def test_go_back_after_navigate(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(HOME)
        p.navigate_to(DOCS)
        p.go_back()
        assert p.current_path == HOME

    def test_go_forward_after_back(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(HOME)
        p.navigate_to(DOCS)
        p.go_back()
        p.go_forward()
        assert p.current_path == DOCS

    def test_navigate_clears_forward_stack(self, env):
        p, _view, _vfs, _ = env
        p.navigate_to(HOME)
        p.navigate_to(DOCS)
        p.go_back()
        p.navigate_to(ROOT)  # new navigate clears forward
        assert not p.can_go_forward

    def test_can_go_back_and_forward_properties(self, env):
        p, _view, _vfs, _ = env
        assert not p.can_go_back
        assert not p.can_go_forward
        p.navigate_to(HOME)
        p.navigate_to(DOCS)
        assert p.can_go_back
        p.go_back()
        assert p.can_go_forward

    def test_navigate_permission_denied_no_back_stack(self, env):
        p, _view, vfs, _ = env
        p.navigate_to(HOME)
        vfs.deny(DOCS)
        p.navigate_to(DOCS)
        assert not p.can_go_back


class TestMarks:
    """TC-style mark/selection tests."""

    def test_toggle_mark_adds_path(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        assert HOME / "readme.txt" in p.marks

    def test_toggle_mark_removes_on_second_call(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        p.toggle_mark()
        assert len(p.marks) == 0

    def test_toggle_mark_skips_dotdot(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = FileItem(name="..", path=ROOT, is_dir=True, size=0, modified=0.0)
        p.toggle_mark()
        assert len(p.marks) == 0
        assert view.cursor_advances == 0

    def test_toggle_mark_advances_cursor(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        assert view.cursor_advances == 1

    def test_select_all(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        p.select_all()
        # _items = archive, docs, readme.txt, zebra.txt (4 items, no "..")
        assert len(p.marks) == 4
        assert HOME / "readme.txt" in p.marks
        assert HOME / "archive" in p.marks

    def test_deselect_all(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        p.select_all()
        p.deselect_all()
        assert len(p.marks) == 0

    def test_invert_selection(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        p.invert_selection()
        # readme.txt was marked → now unmarked; others now marked
        assert HOME / "readme.txt" not in p.marks
        assert HOME / "zebra.txt" in p.marks
        assert HOME / "archive" in p.marks
        assert HOME / "docs" in p.marks
        assert len(p.marks) == 3

    def test_select_by_pattern(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        p.select_by_pattern("*.txt")
        assert HOME / "readme.txt" in p.marks
        assert HOME / "zebra.txt" in p.marks
        assert HOME / "docs" not in p.marks
        assert HOME / "archive" not in p.marks

    def test_deselect_by_pattern(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        p.select_all()
        p.deselect_by_pattern("*.txt")
        assert HOME / "readme.txt" not in p.marks
        assert HOME / "zebra.txt" not in p.marks
        assert HOME / "archive" in p.marks
        assert HOME / "docs" in p.marks

    def test_marks_cleared_on_navigate_new_path(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        assert HOME / "readme.txt" in p.marks
        p.navigate_to(DOCS)
        assert len(p.marks) == 0

    def test_marks_kept_on_refresh(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        assert HOME / "readme.txt" in p.marks
        p.refresh()
        assert HOME / "readme.txt" in p.marks

    def test_marked_items_property(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        result = p.marked_items
        assert len(result) == 1
        assert result[0].name == "readme.txt"

    def test_status_shows_marked_count(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark()
        assert "marked" in view.status
        assert "4 items" in view.status

    def test_status_shows_items_count(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        assert "4 items" in view.status

    def test_toggle_mark_up_marks_and_retreats(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = _item("readme.txt", HOME, size=100)
        p.toggle_mark_up()
        assert HOME / "readme.txt" in p.marks
        assert view.cursor_retreats == 1

    def test_toggle_mark_up_skips_dotdot(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        view.cursor = FileItem(name="..", path=ROOT, is_dir=True, size=0, modified=0.0)
        p.toggle_mark_up()
        assert len(p.marks) == 0

    def test_fmt_size_bytes(self):
        from biome_fm.presenters.pane_presenter import PanePresenter
        assert PanePresenter._fmt_size(500) == "500 B"

    def test_fmt_size_mb(self):
        from biome_fm.presenters.pane_presenter import PanePresenter
        assert "MB" in PanePresenter._fmt_size(2_500_000)


class TestNavHistory:
    def test_navigate_pushes_history(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        assert HOME in view.nav_history

    def test_history_deduplicates(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        p.navigate_to(DOCS)
        p.navigate_to(HOME)
        assert view.nav_history.count(HOME) == 1

    def test_history_most_recent_first(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME)
        p.navigate_to(DOCS)
        assert view.nav_history[0] == DOCS

    def test_history_capped_at_30_visible(self, env):
        p, view, vfs, _ = env
        for i in range(35):
            d = HOME / f"dir{i}"
            vfs._tree[d] = []
            p.navigate_to(d)
        assert len(view.nav_history) == 30

    def test_internal_history_capped_at_60(self, env):
        p, view, vfs, _ = env
        for i in range(65):
            d = HOME / f"dir{i}"
            vfs._tree[d] = []
            p.navigate_to(d)
        assert len(p._nav_history) == 60

    def test_failed_navigate_no_history(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(HOME / "nonexistent_xyz")
        assert len(view.nav_history) == 0


class TestOpenerGuard:
    """Bug fixes: .7z not navigated; virtual paths show error instead of crashing."""

    def _presenter(self, opener=None):
        from biome_fm.presenters.pane_presenter import PanePresenter
        vfs = FakeVFS({HOME: []})
        view = FakePaneView()
        p = PanePresenter(view=view, vfs=vfs, home=HOME, opener=opener)
        p.navigate_to(HOME)
        return p, view

    def test_7z_file_calls_opener(self, tmp_path):
        """After removing .7z from _ARCHIVE_SUFFIXES, opener must be called."""
        called = []
        sevenz = tmp_path / "archive.7z"
        sevenz.touch()
        item = FileItem(name="archive.7z", path=sevenz, is_dir=False, size=0, modified=0.0)
        p, view = self._presenter(opener=called.append)
        p.on_item_activated(item)
        assert called == [sevenz]
        assert not view.errors

    def test_file_inside_archive_shows_error(self):
        """Virtual path (non-existent on disk) shows error, does not call opener."""
        called = []
        virtual = Path("/fake/archive.zip/inner/file.txt")
        item = FileItem(name="file.txt", path=virtual, is_dir=False, size=0, modified=0.0)
        p, view = self._presenter(opener=called.append)
        p.on_item_activated(item)
        assert called == []
        assert "extract" in view.status

    def test_real_file_calls_opener_regression(self, tmp_path):
        """Real existing file must still reach opener (regression guard)."""
        called = []
        real = tmp_path / "notes.txt"
        real.write_text("hi")
        item = FileItem(name="notes.txt", path=real, is_dir=False, size=2, modified=0.0)
        p, view = self._presenter(opener=called.append)
        p.on_item_activated(item)
        assert called == [real]
        assert not view.errors


class TestGoUpSelection:
    def test_go_up_selects_previous_folder(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(DOCS)
        p.go_up()
        assert view.selected == "docs"

    def test_go_up_from_root_keeps_first(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(ROOT)
        p.go_up()
        assert view.selected == "home"

    def test_go_up_via_dotdot_selects_previous(self, env):
        p, view, _vfs, _ = env
        p.navigate_to(DOCS)
        dotdot = FileItem(name="..", path=HOME, is_dir=True, size=0, modified=0.0)
        p.on_item_activated(dotdot)
        assert view.selected == "docs"
