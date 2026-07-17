"""Unit tests for AIPresenter.build_rename_regex (Feature #81)."""
from __future__ import annotations

import json

import pytest

from biome_fm.presenters.ai_presenter import AIPresenter


class _MockProvider:
    name = "mock"
    models = ["m"]
    active_model = "m"
    available = True
    supports_events = False

    def __init__(self, response: str) -> None:
        self._response = response
        self.last_messages: list[dict] = []

    def chat(self, messages, system=""):
        self.last_messages = messages
        return self._response

    def chat_stream(self, messages, system=""):
        return iter([])

    def set_model(self, model):
        pass


class _NullView:
    def append_message(self, *a): pass
    def set_busy(self, *a): pass
    def append_token(self, *a): pass
    def finalize_stream(self): pass
    def discard_stream(self): pass
    def add_attachment_chip(self, *a): pass
    def clear_attachment_chips(self): pass
    def set_provider_list(self, *a): pass
    def append_tool_event(self, *a): pass


def _presenter(response: str) -> tuple[AIPresenter, _MockProvider]:
    p = _MockProvider(response)
    return AIPresenter(_NullView(), {"mock": p}), p


def test_parses_json_response():
    payload = json.dumps({"pattern": r"\d+", "replacement": "NUM"})
    ai, provider = _presenter(payload)
    pattern, replacement = ai.build_rename_regex(["file1.txt", "file2.txt"], "replace numbers")
    assert pattern == r"\d+"
    assert replacement == "NUM"
    # check prompt contains filenames and instruction
    content = provider.last_messages[0]["content"]
    assert "file1.txt" in content
    assert "replace numbers" in content


def test_invalid_json_raises():
    ai, _ = _presenter("not json at all")
    with pytest.raises(ValueError, match="Invalid AI response"):
        ai.build_rename_regex(["a.txt"], "do something")
