"""TDD: search history dedup + max — no Qt."""
from __future__ import annotations

from biome_fm.presenters.search_coordinator import add_to_history


def test_history_dedup_and_order() -> None:
    result = add_to_history(["b", "c"], "b")
    assert result == ["b", "c"]  # moved to front, deduped


def test_new_query_goes_to_front() -> None:
    result = add_to_history(["a", "b"], "new")
    assert result[0] == "new"
    assert "a" in result and "b" in result


def test_history_max_30() -> None:
    history = [str(i) for i in range(30)]
    result = add_to_history(history, "extra")
    assert len(result) == 30
    assert result[0] == "extra"


def test_empty_history() -> None:
    result = add_to_history([], "first")
    assert result == ["first"]
