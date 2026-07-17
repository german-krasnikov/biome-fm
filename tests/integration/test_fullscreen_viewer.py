"""Integration tests — FullscreenViewer dialog."""
from __future__ import annotations

import pytest
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.qt import QDialog, Qt


def _item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=is_dir, size=0, modified=0.0)


def _render(req: PreviewRequest) -> PreviewResult:
    return PreviewResult(kind=ContentKind.TEXT, data="test content")


@pytest.fixture
def items():
    return [_item("a.txt"), _item("b.txt"), _item("c.txt"), _item("d.txt"), _item("e.txt")]


@pytest.fixture
def viewer(qtbot, items):
    from biome_fm.views.fullscreen_viewer import FullscreenViewer
    w = FullscreenViewer(items, 1, _render)
    qtbot.addWidget(w)
    return w


def test_opens_as_dialog(viewer):
    assert isinstance(viewer, QDialog)


def test_escape_closes(viewer, qtbot):
    viewer.show()
    qtbot.keyPress(viewer, Qt.Key.Key_Escape)
    assert not viewer.isVisible()


def test_f11_closes(viewer, qtbot):
    viewer.show()
    qtbot.keyPress(viewer, Qt.Key.Key_F11)
    assert not viewer.isVisible()


def test_right_arrow_advances(viewer):
    assert viewer._idx == 1
    viewer._go(1)
    assert viewer._idx == 2


def test_left_arrow_decrements(viewer):
    assert viewer._idx == 1
    viewer._go(-1)
    assert viewer._idx == 0


def test_title_format(items):
    from biome_fm.views.fullscreen_viewer import FullscreenViewer
    w = FullscreenViewer(items, 1, _render)
    # idx=1 → "b.txt (2/5)"
    assert w.windowTitle() == "b.txt (2/5)"


def test_wraps_around(items):
    from biome_fm.views.fullscreen_viewer import FullscreenViewer
    w = FullscreenViewer(items, 4, _render)  # last item
    assert w._idx == 4
    w._go(1)
    assert w._idx == 0  # wraps to first
