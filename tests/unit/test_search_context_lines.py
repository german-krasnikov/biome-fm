"""Tests for context-lines feature in content search."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter


FIVE_LINES = "aaa\nbbb\nMATCH here\nddd\neee\n"


@pytest.fixture()
def presenter(tmp_path: Path) -> SearchPresenter:
    return SearchPresenter(LocalVFS(), tmp_path)


def write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# --- CONTENT mode ---

def test_context_before_and_after(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", FIVE_LINES)
    results = presenter.search("MATCH", mode=SearchMode.CONTENT, context_lines=2)
    assert len(results) == 1
    ctx = results[0].context
    assert "aaa" in ctx
    assert "MATCH here" in ctx
    assert "eee" in ctx
    assert ctx.count("\n") == 4  # 5 lines → 4 newlines


def test_context_at_file_start(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", "MATCH\nline2\nline3\nline4\n")
    results = presenter.search("MATCH", mode=SearchMode.CONTENT, context_lines=2)
    assert len(results) == 1
    lines = results[0].context.split("\n")
    assert lines[0] == "MATCH"
    assert len(lines) == 3  # no lines before, 2 after


def test_context_at_file_end(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", "line1\nline2\nline3\nMATCH\n")
    results = presenter.search("MATCH", mode=SearchMode.CONTENT, context_lines=2)
    assert len(results) == 1
    lines = results[0].context.split("\n")
    assert lines[-1] == "MATCH"
    assert len(lines) == 3  # 2 before, no lines after


def test_zero_context_returns_match_only(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", FIVE_LINES)
    results = presenter.search("MATCH", mode=SearchMode.CONTENT, context_lines=0)
    assert len(results) == 1
    assert "\n" not in results[0].context
    assert "MATCH here" in results[0].context


def test_context_lines_join_format(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", "before\nMATCH\nafter\n")
    results = presenter.search("MATCH", mode=SearchMode.CONTENT, context_lines=1)
    assert len(results) == 1
    assert results[0].context == "before\nMATCH\nafter"


# --- CONTENT_REGEX mode ---

def test_regex_context_before_and_after(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", FIVE_LINES)
    results = presenter.search(r"MATCH \w+", mode=SearchMode.CONTENT_REGEX, context_lines=2)
    assert len(results) == 1
    ctx = results[0].context
    assert "aaa" in ctx
    assert "MATCH here" in ctx
    assert "eee" in ctx


def test_regex_zero_context(tmp_path: Path, presenter: SearchPresenter) -> None:
    write(tmp_path, "f.txt", FIVE_LINES)
    results = presenter.search(r"MATCH", mode=SearchMode.CONTENT_REGEX, context_lines=0)
    assert len(results) == 1
    assert "\n" not in results[0].context
    assert "MATCH" in results[0].context
