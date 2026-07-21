"""Integration tests for F451 — file selection export to clipboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

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

    def set_items(self, items, **kwargs): self.items = items
    def set_path(self, p): self.path = p
    def set_status(self, t): ...
    def show_error(self, m): ...
    def set_marked(self, paths): self._marks = paths
    def current_cursor_item(self): return self._cursor
    def advance_cursor(self): ...
    def retreat_cursor(self): ...
    def set_filter_visible(self, v): ...
    def set_nav_history(self, paths): ...
    def select_item(self, name): ...


def _copy_path_with_marks(presenter: PanePresenter) -> str:
    """Mirrors the updated _copy_path logic from app.py."""
    items = presenter.marked_items
    if items:
        text = "\n".join(str(i.path) for i in items)
    else:
        item = presenter.current_item()
        text = str(item.path) if item is not None else str(presenter.current_path)
    QApplication.clipboard().setText(text)
    return text


@pytest.fixture()
def presenter(tmp_path: Path):
    (tmp_path / "alpha.txt").write_text("a")
    (tmp_path / "beta.txt").write_text("b")
    view = _FakeView()
    p = PanePresenter(view, LocalVFS())
    p.navigate_to(tmp_path)
    view._cursor = FileItem("alpha.txt", tmp_path / "alpha.txt", False, 1, 0.0)
    return p


def test_clipboard_receives_paths(qtbot, presenter, tmp_path):
    presenter.toggle_mark_at(FileItem("alpha.txt", tmp_path / "alpha.txt", False, 1, 0.0))
    presenter.toggle_mark_at(FileItem("beta.txt", tmp_path / "beta.txt", False, 1, 0.0))
    result = _copy_path_with_marks(presenter)
    assert QApplication.clipboard().text() == result
    assert str(tmp_path / "alpha.txt") in result
    assert str(tmp_path / "beta.txt") in result
    assert str(tmp_path) in result  # full paths, not just names


def test_export_fallback_to_cursor(qtbot, presenter, tmp_path):
    # no marks — falls back to cursor path
    result = _copy_path_with_marks(presenter)
    assert result == str(tmp_path / "alpha.txt")
    assert QApplication.clipboard().text() == str(tmp_path / "alpha.txt")
