"""Test that cursor_changed wires to ai_presenter.set_context."""
from __future__ import annotations

from pathlib import Path

from biome_fm.app import _wire_ai_cursor


class _FakeSig:
    def __init__(self):
        self._cbs = []

    def connect(self, cb):
        self._cbs.append(cb)

    def emit(self, item):
        for cb in self._cbs:
            cb(item)


class _FakeView:
    def __init__(self):
        self.cursor_changed = _FakeSig()


class _FakeTabs:
    current_path = Path("/home/user/docs")


class _FakeAI:
    def __init__(self):
        self.calls: list[tuple] = []

    def set_context(self, cwd, selected):
        self.calls.append((cwd, selected))


def test_set_context_called_with_cwd_and_items():
    view = _FakeView()
    tabs = _FakeTabs()
    ai = _FakeAI()

    _wire_ai_cursor(view, tabs, ai)

    from biome_fm.models.file_item import FileItem
    item = FileItem("report.pdf", Path("/home/user/docs/report.pdf"), False, 100, 0.0)
    view.cursor_changed.emit(item)

    assert len(ai.calls) == 1
    cwd, selected = ai.calls[0]
    assert cwd == Path("/home/user/docs")
    assert selected == [item]


def test_set_context_empty_on_none_cursor():
    view = _FakeView()
    tabs = _FakeTabs()
    ai = _FakeAI()

    _wire_ai_cursor(view, tabs, ai)
    view.cursor_changed.emit(None)

    assert ai.calls[0] == (Path("/home/user/docs"), [])
