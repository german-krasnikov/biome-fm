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
