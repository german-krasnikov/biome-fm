"""Unit tests for cancel/epoch logic in AIPresenter — no Qt."""
from __future__ import annotations

from biome_fm.presenters.ai_presenter import AIPresenter, _AIEvent


class _MockProvider:
    name = "mock"
    models: list[str] = ["m"]  # noqa: RUF012
    active_model = "m"
    available = True

    def __init__(self, tokens=("ok",)):
        self._tokens = tokens

    def chat_stream(self, messages, system=""):
        yield from self._tokens

    def set_model(self, model):
        pass


class _MockView:
    def __init__(self):
        self.messages: list = []
        self.busy: list = []
        self.tokens: list = []
        self.finalized = 0
        self.discarded = 0

    def append_message(self, role, content):
        self.messages.append((role, content))

    def set_busy(self, b):
        self.busy.append(b)

    def append_token(self, t):
        self.tokens.append(t)

    def finalize_stream(self):
        self.finalized += 1

    def add_attachment_chip(self, n):
        pass

    def clear_attachment_chips(self):
        pass

    def set_provider_list(self, *a):
        pass

    def append_tool_event(self, d):
        pass

    def discard_stream(self):
        self.discarded += 1


def _make():
    provider = _MockProvider()
    view = _MockView()
    presenter = AIPresenter(view, {"mock": provider}, "mock")
    return presenter, view, provider


def test_epoch_increments_on_cancel():
    presenter, _, _ = _make()
    initial = presenter._epoch
    presenter.cancel()
    assert presenter._epoch == initial + 1


def test_cancel_clears_buffer():
    presenter, view, _ = _make()
    presenter._stream_buffer[:] = ["a", "b"]
    presenter.cancel()
    assert presenter._stream_buffer == []
    assert view.discarded == 1


def test_stale_events_dropped():
    presenter, view, _ = _make()
    presenter._epoch = 2  # current epoch
    # stale token (epoch=1) and current token (epoch=2)
    presenter._events.put(_AIEvent("token", "stale", epoch=1))
    presenter._events.put(_AIEvent("token", "current", epoch=2))
    presenter._events.put(_AIEvent("done", epoch=2))
    presenter.drain()
    assert "stale" not in view.tokens
    assert "current" in view.tokens
