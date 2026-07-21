"""F416 — Tail mode unit tests (Qt-free)."""
import queue
from unittest.mock import Mock

from biome_fm.preview.presenter import PreviewPresenter
from biome_fm.preview.provider import ContentKind, PreviewResult
from biome_fm.preview.registry import PreviewRegistry


def _make_presenter():
    view = Mock()
    view.is_panel_visible.return_value = True
    registry = Mock(spec=PreviewRegistry)
    return PreviewPresenter(view=view, registry=registry)


def test_set_tail_mode_true():
    p = _make_presenter()
    p.set_tail_mode(True)
    assert p._tail_mode is True


def test_set_tail_mode_false():
    p = _make_presenter()
    p.set_tail_mode(True)
    p.set_tail_mode(False)
    assert p._tail_mode is False


def test_drain_scrolls_when_tail_on():
    p = _make_presenter()
    p.set_tail_mode(True)
    result = PreviewResult(kind=ContentKind.TEXT, data="hello")
    p._queue.put(result)
    p.drain()
    p._view.scroll_to_bottom.assert_called_once()


def test_drain_no_scroll_when_tail_off():
    p = _make_presenter()
    result = PreviewResult(kind=ContentKind.TEXT, data="hello")
    p._queue.put(result)
    p.drain()
    p._view.scroll_to_bottom.assert_not_called()
