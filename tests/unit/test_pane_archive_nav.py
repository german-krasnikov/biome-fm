"""Unit tests for PanePresenter archive navigation. No Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter, _is_archive


def _item(name: str, parent: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=0, modified=0.0)


class FakeVFS:
    def __init__(self, tree: dict[Path, list[FileItem]]) -> None:
        self._tree = tree

    def listdir(self, path: Path) -> list[FileItem]:
        if path not in self._tree:
            raise FileNotFoundError(path)
        return list(self._tree[path])

    def exists(self, p: Path) -> bool:
        return p in self._tree
    def copy(self, s, d): ...
    def move(self, s, d): ...
    def delete(self, p): ...
    def mkdir(self, p): ...
    def stat(self, p): ...  # type: ignore[return]


@dataclass
class FakePaneView:
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    errors: list[str] = field(default_factory=list)
    status: str = ""
    marked: set[Path] = field(default_factory=set)
    cursor: FileItem | None = None
    cursor_advances: int = 0

    def set_items(self, items, **kwargs): self.items = list(items)
    def set_path(self, path): self.path = path
    def show_error(self, msg): self.errors.append(msg)
    def set_status(self, text): self.status = text
    def set_marked(self, paths): self.marked = set(paths)
    def current_cursor_item(self): return self.cursor
    def advance_cursor(self): self.cursor_advances += 1
    def retreat_cursor(self): pass
    def set_filter_visible(self, visible: bool) -> None: pass
    def set_nav_history(self, paths: list) -> None: pass
    def select_item(self, name: str) -> None: pass


HOME = Path("/home")
ARCHIVE = HOME / "data.zip"
INSIDE = ARCHIVE  # after navigating in, cwd = archive path


@pytest.fixture
def env():
    tree: dict[Path, list[FileItem]] = {
        HOME: [
            _item("data.zip", HOME),
            _item("notes.tar.gz", HOME),
            _item("readme.txt", HOME),
            _item("subdir", HOME, is_dir=True),
        ],
        ARCHIVE: [],  # archive contents (empty for nav test)
        HOME / "notes.tar.gz": [],
        HOME / "subdir": [],
    }
    vfs = FakeVFS(tree)
    view = FakePaneView()
    p = PanePresenter(view=view, vfs=vfs, home=HOME)
    p.navigate_to(HOME)
    return p, view


class TestArchiveNav:
    def test_activate_zip_navigates(self, env):
        p, _ = env
        p.on_item_activated(_item("data.zip", HOME))
        assert p.current_path == HOME / "data.zip"

    def test_activate_tar_gz_navigates(self, env):
        p, _ = env
        p.on_item_activated(_item("notes.tar.gz", HOME))
        assert p.current_path == HOME / "notes.tar.gz"

    def test_go_up_from_archive(self, env):
        p, _ = env
        p.on_item_activated(_item("data.zip", HOME))
        assert p.current_path == ARCHIVE
        p.go_up()
        assert p.current_path == HOME

    def test_activate_regular_file_unchanged(self, env):
        p, _ = env
        p.on_item_activated(_item("readme.txt", HOME))
        assert p.current_path == HOME

    def test_is_archive_detection(self):
        assert _is_archive(Path("/a/file.zip"))
        assert _is_archive(Path("/a/file.tar"))
        assert _is_archive(Path("/a/file.tar.gz"))
        assert _is_archive(Path("/a/file.tar.bz2"))
        assert _is_archive(Path("/a/file.tar.xz"))
        assert not _is_archive(Path("/a/file.7z"))  # .7z falls through to system opener
        assert not _is_archive(Path("/a/readme.txt"))
        assert not _is_archive(Path("/a/image.png"))
