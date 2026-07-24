"""Unit tests for async AI rename and dead code removal — scenarios 7-8."""
from __future__ import annotations

import queue
from unittest.mock import MagicMock


def test_suggest_renames_queued():
    """suggest_renames result can be queued — simulates pool submit pattern."""
    from biome_fm.presenters.ai_rename_presenter import suggest_renames

    provider = MagicMock()
    provider.available = True
    provider.chat.return_value = '["new_a.txt", null, "new_c.txt"]'
    names = ["a.txt", "b.txt", "c.txt"]

    result_q: queue.SimpleQueue = queue.SimpleQueue()
    result_q.put(suggest_renames(names, provider))

    suggestions = result_q.get_nowait()
    assert suggestions[0] == "new_a.txt"
    assert suggestions[1] is None
    assert suggestions[2] == "new_c.txt"


def test_build_rename_regex_removed():
    """Confirm dead method build_rename_regex is gone."""
    from biome_fm.presenters.ai_presenter import AIPresenter
    assert not hasattr(AIPresenter, "build_rename_regex")
