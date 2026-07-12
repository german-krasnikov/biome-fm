"""Unit tests for opener utility and PanePresenter file opening. No Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


def _item(name: str, parent: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=0, modified=0.0)


class FakeVFS:
    def __init__(self, tree):
        self._tree = tree
    def listdir(self, path):
        if path not in self._tree:
            raise FileNotFoundError(path)
        return list(self._tree[path])
    def exists(self, p): return p in self._tree
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

    def set_items(self, items): self.items = list(items)
    def set_path(self, path): self.path = path
    def show_error(self, msg): self.errors.append(msg)
    def set_status(self, text): self.status = text
    def set_marked(self, paths): self.marked = set(paths)
    def current_cursor_item(self): return self.cursor
    def advance_cursor(self): self.cursor_advances += 1
    def retreat_cursor(self): pass
    def set_filter_visible(self, visible: bool) -> None: pass
    def set_nav_history(self, paths: list) -> None: pass


HOME = Path("/home")


@pytest.fixture
def env():
    tree = {
        HOME: [_item("doc.pdf", HOME), _item("subdir", HOME, is_dir=True)],
        HOME / "subdir": [],
    }
    vfs = FakeVFS(tree)
    view = FakePaneView()
    opened: list[Path] = []
    p = PanePresenter(view=view, vfs=vfs, home=HOME, opener=opened.append)
    p.navigate_to(HOME)
    return p, opened


class TestOpener:
    def test_open_file_mac_uses_open(self):
        from biome_fm.utils.opener import open_file
        with patch("subprocess.Popen") as mock_popen, patch("sys.platform", "darwin"):
            open_file(Path("/tmp/doc.pdf"))
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args[0][0]
            assert cmd[0] == "open"

    def test_open_file_calls_subprocess(self):
        from biome_fm.utils.opener import open_file
        with patch("subprocess.Popen") as mock_popen, patch("sys.platform", "linux"):
            open_file(Path("/tmp/doc.pdf"))
            mock_popen.assert_called_once()

    def test_activate_file_calls_opener(self, env):
        p, opened = env
        p.on_item_activated(_item("doc.pdf", HOME))
        assert Path("/home/doc.pdf") in opened

    def test_activate_dir_does_not_call_opener(self, env):
        p, opened = env
        p.on_item_activated(_item("subdir", HOME, is_dir=True))
        assert opened == []
        assert p.current_path == HOME / "subdir"
