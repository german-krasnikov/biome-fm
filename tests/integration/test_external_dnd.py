"""Integration tests: outbound drag-and-drop MIME data for external targets."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.qt import QApplication, Qt
from biome_fm.views.pane_view import PaneView


def _item(name: str, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path("/tmp") / name, is_dir=is_dir, size=100, modified=1.0)


@pytest.fixture
def pane(qapp, qtbot):
    view = PaneView()
    qtbot.addWidget(view)
    view.set_items([_item("a.txt"), _item("b.py"), _item("subdir", is_dir=True)])
    view.show()
    return view


def _mime_from_selection(pane: PaneView):
    table = pane._table
    table.selectAll()
    indexes = table.selectedIndexes()
    return table.mimeData(indexes)


class TestExternalDnDMime:
    def test_has_internal_mime(self, pane):
        mime = _mime_from_selection(pane)
        assert mime.hasFormat("application/x-biome-fm-paths")

    def test_has_urls(self, pane):
        mime = _mime_from_selection(pane)
        assert mime.hasUrls()
        url_paths = {u.toLocalFile() for u in mime.urls()}
        assert "/tmp/a.txt" in url_paths
        assert "/tmp/b.py" in url_paths

    def test_urls_exclude_dotdot(self, pane):
        # '..' is not a real path — must not appear in URL list
        pane.set_items([
            FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0),
            _item("real.txt"),
        ])
        table = pane._table
        table.selectAll()
        mime = table.mimeData(table.selectedIndexes())
        url_paths = {u.toLocalFile() for u in mime.urls()}
        assert "/" not in url_paths
        assert "/tmp/real.txt" in url_paths

    def test_has_text(self, pane):
        mime = _mime_from_selection(pane)
        assert mime.hasText()
        text = mime.text()
        assert "/tmp/a.txt" in text
        assert "/tmp/b.py" in text

    def test_text_paths_newline_separated(self, pane):
        pane.set_items([_item("x.txt"), _item("y.txt")])
        table = pane._table
        table.selectAll()
        mime = table.mimeData(table.selectedIndexes())
        lines = mime.text().splitlines()
        assert len(lines) == 2  # noqa: PLR2004

    def test_alt_drag_no_urls(self, pane, monkeypatch):
        monkeypatch.setattr(
            QApplication, "keyboardModifiers",
            staticmethod(lambda: Qt.KeyboardModifier.AltModifier),
        )
        mime = _mime_from_selection(pane)
        assert not mime.hasUrls()
        assert mime.hasText()
        assert "/tmp/a.txt" in mime.text()


class TestMarkedDnDMime:
    def test_marks_override_selection(self, pane):
        """When marks exist, DnD carries all marked paths, not just cursor."""
        pane.set_marked({Path("/tmp/a.txt"), Path("/tmp/b.py")})
        table = pane._table
        # Cursor on subdir (not marked)
        for row in range(table.model().rowCount()):
            idx = table.model().index(row, 0)
            src = pane._proxy.mapToSource(idx)
            item = pane._model.item_at(src.row())
            if item and item.name == "subdir":
                table.setCurrentIndex(idx)
                break
        mime = table.mimeData(table.selectedIndexes())
        raw = mime.data("application/x-biome-fm-paths").data().decode()
        paths = set(raw.splitlines())
        assert "/tmp/a.txt" in paths
        assert "/tmp/b.py" in paths
        assert "/tmp/subdir" not in paths

    def test_empty_marks_falls_back_to_indexes(self, pane):
        """No marks -> original behavior: only selected rows in mime."""
        pane.set_marked(set())
        table = pane._table
        table.selectAll()
        mime = table.mimeData(table.selectedIndexes())
        raw = mime.data("application/x-biome-fm-paths").data().decode()
        paths = set(raw.splitlines())
        assert "/tmp/a.txt" in paths
        assert "/tmp/b.py" in paths
        assert "/tmp/subdir" in paths

    def test_marks_exclude_dotdot(self, pane):
        """'..' must never appear in DnD mime data even if somehow marked."""
        pane.set_items([
            FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0),
            _item("real.txt"),
        ])
        pane.set_marked({Path("/"), Path("/tmp/real.txt")})
        table = pane._table
        mime = table.mimeData(table.selectedIndexes())
        raw = mime.data("application/x-biome-fm-paths").data().decode()
        paths = set(raw.splitlines())
        assert "/" not in paths
        assert "/tmp/real.txt" in paths

    def test_marked_count_in_urls(self, pane):
        """Exactly N marks -> exactly N URLs."""
        pane.set_marked({Path("/tmp/a.txt"), Path("/tmp/b.py")})
        table = pane._table
        mime = table.mimeData(table.selectedIndexes())
        assert len(mime.urls()) == 2
