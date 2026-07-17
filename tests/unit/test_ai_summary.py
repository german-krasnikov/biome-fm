"""Tests for AIPresenter.summarize_file — pure Python, no Qt."""
from __future__ import annotations

import time
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.ai_presenter import AIPresenter


class _Provider:
    available = True
    models = ["m"]
    active_model = "m"

    def __init__(self):
        self.calls = 0

    def chat_stream(self, messages, system=""):
        self.calls += 1
        yield "Summary text"

    def set_model(self, m):
        pass


class _View:
    def __init__(self):
        self.messages = []
        self.busy = []
        self.tokens = []
        self.finalized = 0

    def append_message(self, role, content):
        self.messages.append((role, content))

    def set_busy(self, b):
        self.busy.append(b)

    def append_token(self, t):
        self.tokens.append(t)

    def finalize_stream(self):
        self.finalized += 1

    def discard_stream(self):
        pass

    def clear_attachment_chips(self):
        pass

    def add_attachment_chip(self, name):
        pass

    def set_provider_list(self, *a):
        pass

    def append_tool_event(self, desc):
        pass


def _item(mtime=1.0):
    return FileItem(name="file.txt", path=Path("/tmp/file.txt"),
                    is_dir=False, size=42, modified=mtime)


def _make():
    provider = _Provider()
    view = _View()
    presenter = AIPresenter(view, {"mock": provider}, "mock")
    return presenter, view, provider


def _drain(p: AIPresenter):
    p._pool.shutdown(wait=True)
    p.drain()


def test_summarize_sends_prompt():
    presenter, view, provider = _make()
    presenter.summarize_file(_item())
    _drain(presenter)
    # user message must reference summarize intent
    assert any("ummariz" in m[1] for m in view.messages)
    assert provider.calls == 1


def test_summarize_uses_cache():
    presenter, view, provider = _make()
    item = _item()
    # first call
    presenter.summarize_file(item)
    _drain(presenter)
    first_calls = provider.calls

    # second call — same (path, mtime) should hit cache
    presenter.summarize_file(item)
    _drain(presenter)
    assert provider.calls == first_calls  # no extra AI call


def test_summarize_no_provider_no_crash():
    view = _View()
    presenter = AIPresenter(view, {}, "none")
    item = _item()
    # must not raise
    presenter.summarize_file(item)
    # no provider → shows not-configured message or just returns
    # either way, no exception
