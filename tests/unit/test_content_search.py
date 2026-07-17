"""Tests for content search with regex and line numbers."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter


@pytest.fixture()
def src_file(tmp_path: Path) -> Path:
    f = tmp_path / "source.py"
    f.write_text("line one\ndef foo():\n    return 42\n")
    return tmp_path


def test_content_regex_match(src_file: Path) -> None:
    results = SearchPresenter(LocalVFS(), src_file).search(
        r"def \w+", mode=SearchMode.CONTENT_REGEX
    )
    assert len(results) == 1
    assert results[0].item.name == "source.py"


def test_content_regex_invalid_no_crash(src_file: Path) -> None:
    # Invalid regex should not raise, just return no results
    results = SearchPresenter(LocalVFS(), src_file).search(
        r"[invalid", mode=SearchMode.CONTENT_REGEX
    )
    assert results == []


def test_line_number_in_context(src_file: Path) -> None:
    results = SearchPresenter(LocalVFS(), src_file).search(
        r"def \w+", mode=SearchMode.CONTENT_REGEX
    )
    assert len(results) == 1
    # context must contain line number prefix ":N:"
    assert results[0].context.startswith(":2:")
