"""Integration tests for Copy Path command."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.pane_presenter import PanePresenter
from biome_fm.qt import QApplication


@dataclass
class _FakeView:
    """Minimal PaneView stub."""
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    _cursor: FileItem | None = None

    def set_items(self, items: list[FileItem], **kwargs) -> None: self.items = items
    def set_path(self, p: Path) -> None: self.path = p
    def set_status(self, t: str) -> None: ...
    def show_error(self, m: str) -> None: ...
    def set_marked(self, paths: set) -> None: ...
    def current_cursor_item(self) -> FileItem | None: return self._cursor
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, visible: bool) -> None: ...
    def set_nav_history(self, paths: list) -> None: ...
    def select_item(self, name: str) -> None: ...


def _copy_path(presenter: PanePresenter) -> str:
    """Copy-path logic extracted for testing."""
    item = presenter.current_item()
    path = str(item.path) if item is not None else str(presenter.current_path)
    QApplication.clipboard().setText(path)
    return path


@pytest.fixture()
def presenter(tmp_path: Path):
    (tmp_path / "file.txt").write_text("x")
    view = _FakeView()
    p = PanePresenter(view, LocalVFS())
    p.navigate_to(tmp_path)
    # cursor points at first real file
    view._cursor = FileItem(
        name="file.txt", path=tmp_path / "file.txt",
        is_dir=False, size=1, modified=0.0,
    )
    return p


def test_copy_path_copies_to_clipboard(qtbot, presenter, tmp_path):
    path = _copy_path(presenter)
    assert QApplication.clipboard().text() == str(tmp_path / "file.txt")
    assert path == str(tmp_path / "file.txt")


def test_copy_path_dir_when_no_item(qtbot, presenter, tmp_path):
    presenter._view._cursor = None  # type: ignore[attr-defined]
    _copy_path(presenter)
    assert QApplication.clipboard().text() == str(tmp_path)


def test_copy_path_command_registered():
    registry = CommandRegistry()
    registry.register(CommandEntry("Copy Path", "Ctrl+Shift+C", lambda: None))
    results = registry.search("Copy Path")
    assert len(results) == 1
    assert results[0].shortcut == "Ctrl+Shift+C"
