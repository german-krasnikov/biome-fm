"""Unit tests for ai_rename_presenter.suggest_renames."""
import json

import pytest

from biome_fm.presenters.ai_rename_presenter import suggest_renames


class _MockProvider:
    available = True

    def __init__(self, response: str) -> None:
        self._response = response

    def chat(self, messages, system=""):
        return self._response


class _NoOp:
    available = False

    def chat(self, messages, system=""):
        return ""


def test_noop_returns_none_list():
    result = suggest_renames(["a.txt", "b.jpg"], _NoOp())
    assert result == [None, None]


def test_valid_json_parsed():
    suggestions = ["alpha.txt", None]
    provider = _MockProvider(json.dumps(suggestions))
    result = suggest_renames(["a.txt", "b.jpg"], provider)
    assert result == ["alpha.txt", None]


def test_malformed_json_fallback():
    provider = _MockProvider("not json at all")
    result = suggest_renames(["a.txt", "b.jpg"], provider)
    assert result == [None, None]


def test_length_mismatch_padded():
    # Provider returns only 1 suggestion for 3 files
    provider = _MockProvider(json.dumps(["better.txt"]))
    result = suggest_renames(["a.txt", "b.jpg", "c.png"], provider)
    assert result == ["better.txt", None, None]


def test_empty_names_returns_empty():
    result = suggest_renames([], _MockProvider("[]"))
    assert result == []
