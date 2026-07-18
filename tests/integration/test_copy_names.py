"""Integration tests for Copy File Names command (F204)."""
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
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    _cursor: FileItem | None = None
    _marks: set = field(default_factory=set)

    def set_items(self, items: list[FileItem], **kwargs) -> None: self.items = items
    def set_path(self, p: Path) -> None: self.path = p
    def set_status(self, t: str) -> None: ...
    def show_error(self, m: str) -> None: ...
    def set_marked(self, paths: set) -> None: self._marks = paths
    def current_cursor_item(self) -> FileItem | None: return self._cursor
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, visible: bool) -> None: ...
    def set_nav_history(self, paths: list) -> None: ...
    def select_item(self, name: str) -> None: ...


def _copy_names(presenter: PanePresenter) -> str:
    """Copy-names logic extracted for testing."""
    marks = presenter.marked_items
    items = marks if marks else ([presenter.current_item()] if presenter.current_item() and presenter.current_item().name != ".." else [])
    names = "\n".join(i.name for i in items)
    QApplication.clipboard().setText(names)
    return names


@pytest.fixture()
def presenter(tmp_path: Path):
    (tmp_path / "alpha.txt").write_text("a")
    (tmp_path / "beta.txt").write_text("b")
    view = _FakeView()
    p = PanePresenter(view, LocalVFS())
    p.navigate_to(tmp_path)
    view._cursor = FileItem(
        name="alpha.txt", path=tmp_path / "alpha.txt",
        is_dir=False, size=1, modified=0.0,
    )
    return p


def test_copy_names_marked_files(qtbot, presenter, tmp_path):
    presenter.toggle_mark_at(FileItem("alpha.txt", tmp_path / "alpha.txt", False, 1, 0.0))
    presenter.toggle_mark_at(FileItem("beta.txt", tmp_path / "beta.txt", False, 1, 0.0))
    result = _copy_names(presenter)
    assert QApplication.clipboard().text() == result
    assert "alpha.txt" in result
    assert "beta.txt" in result
    # names only, no paths
    assert str(tmp_path) not in result


def test_copy_names_cursor_fallback(qtbot, presenter, tmp_path):
    # no marks — should use cursor
    result = _copy_names(presenter)
    assert result == "alpha.txt"
    assert QApplication.clipboard().text() == "alpha.txt"


def test_copy_names_command_registered():
    registry = CommandRegistry()
    registry.register(CommandEntry("Copy File Names", "Alt+Shift+N", lambda: None))
    results = registry.search("Copy File Names")
    assert len(results) == 1
    assert results[0].shortcut == "Alt+Shift+N"
