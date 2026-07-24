"""Tests for AI clear-session feature."""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.presenters.ai_presenter import AIPresenter, Attachment
from pathlib import Path


# ---------------------------------------------------------------------------
# Pure-Python presenter tests
# ---------------------------------------------------------------------------

class _MockProvider:
    name = "mock"
    models = ["m"]
    active_model = "m"
    available = True

    def chat_stream(self, messages, system=""): yield from ()
    def set_model(self, m): pass


class _MockView:
    def __init__(self):
        self.discarded = 0
        self.busy_calls: list[bool] = []
        self.session_cleared = 0

    def append_message(self, role, content): pass
    def set_busy(self, busy): self.busy_calls.append(busy)
    def append_token(self, t): pass
    def finalize_stream(self): pass
    def discard_stream(self): self.discarded += 1
    def add_attachment_chip(self, name): pass
    def clear_attachment_chips(self): pass
    def set_provider_list(self, *a): pass
    def append_tool_event(self, d): pass
    def clear_session(self): self.session_cleared += 1


def _make():
    view = _MockView()
    p = AIPresenter(view, {"mock": _MockProvider()}, "mock")
    return p, view


def test_presenter_clear_session():
    p, view = _make()
    p._history.extend([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}])
    p._pending_attachments.append(Attachment(Path("/tmp/f.txt"), "text", "data"))
    p._stream_buffer.append("partial")

    p.clear_session()

    assert p._history == []
    assert p._pending_attachments == []
    assert p._stream_buffer == []
    assert view.discarded == 1
    assert False in view.busy_calls
    assert view.session_cleared == 1


def test_presenter_clear_increments_epoch():
    p, _ = _make()
    before = p._epoch
    p.clear_session()
    assert p._epoch == before + 1


# ---------------------------------------------------------------------------
# Qt-dependent tests
# ---------------------------------------------------------------------------

def test_chatlog_reset(qtbot):
    from biome_fm.views._chat_log import ChatLog
    log = ChatLog()
    qtbot.addWidget(log)
    log.stream_start()
    assert log._streaming is True

    log.reset()

    assert log._streaming is False
    assert log._buf == []
    assert log._stream_block_start == 0
    assert log._thinking_pos == -1
    assert log.toPlainText() == ""


def test_clear_button_emits_signal(qtbot):
    from biome_fm.views.ai_chat_panel import AIChatPanel
    panel = AIChatPanel()
    qtbot.addWidget(panel)

    with qtbot.waitSignal(panel.session_clear_requested, timeout=1000):
        panel._clear_btn.click()
