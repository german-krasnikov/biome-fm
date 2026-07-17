"""Unit tests for Preview Mode Toggle — Qt-free."""
from pathlib import Path
from unittest.mock import Mock

from biome_fm.models.file_item import FileItem
from biome_fm.preview.presenter import PreviewPresenter
from biome_fm.preview.provider import ContentKind, PreviewMode, PreviewResult
from biome_fm.preview.registry import PreviewRegistry


def _make_item(name: str = "file.txt") -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=10, modified=1.0)


def _make_presenter():
    view = Mock()
    view.is_panel_visible.return_value = True
    registry = Mock(spec=PreviewRegistry)
    registry.find.return_value = Mock(
        render=Mock(return_value=PreviewResult(ContentKind.HTML, "<p>ok</p>"))
    )
    return PreviewPresenter(view=view, registry=registry)


def test_set_mode_text_forces_text():
    p = _make_presenter()
    p.set_mode(PreviewMode.TEXT)
    assert p._forced_mode == PreviewMode.TEXT


def test_set_mode_hex_forces_hex():
    p = _make_presenter()
    p.set_mode(PreviewMode.HEX)
    assert p._forced_mode == PreviewMode.HEX


def test_auto_uses_registry():
    p = _make_presenter()
    p.set_mode(PreviewMode.TEXT)
    p.set_mode(PreviewMode.AUTO)
    assert p._forced_mode == PreviewMode.AUTO
