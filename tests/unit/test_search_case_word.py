"""Unit tests for case sensitivity and whole-word toggles in SearchPresenter."""
from pathlib import Path

import pytest

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter


def _presenter(tmp_path: Path, content: str) -> SearchPresenter:
    (tmp_path / "test.txt").write_text(content)
    return SearchPresenter(LocalVFS(), tmp_path)


def test_case_insensitive_match(tmp_path):
    """Default: case-insensitive — 'FOO' should match 'foo'."""
    p = _presenter(tmp_path, "hello foo world")
    assert len(p.search("FOO", mode=SearchMode.CONTENT)) == 1


def test_case_sensitive_no_cross_match(tmp_path):
    """case_sensitive=True: 'FOO' must NOT match 'foo'."""
    p = _presenter(tmp_path, "hello foo world")
    assert len(p.search("FOO", mode=SearchMode.CONTENT, case_sensitive=True)) == 0


def test_whole_word_no_partial(tmp_path):
    """whole_word=True: 'foo' must NOT match 'foobar'."""
    p = _presenter(tmp_path, "hello foobar world")
    assert len(p.search("foo", mode=SearchMode.CONTENT, whole_word=True)) == 0


def test_whole_word_matches_exact(tmp_path):
    """whole_word=True: 'foo' matches 'foo bar'."""
    p = _presenter(tmp_path, "hello foo world")
    assert len(p.search("foo", mode=SearchMode.CONTENT, whole_word=True)) == 1


def test_case_insensitive_whole_word_combined(tmp_path):
    """case_sensitive=False + whole_word=True: 'foo' matches 'FOO bar'."""
    p = _presenter(tmp_path, "hello FOO world")
    assert len(p.search("foo", mode=SearchMode.CONTENT, whole_word=True, case_sensitive=False)) == 1


def test_name_regex_case_insensitive(tmp_path):
    (tmp_path / "FooBar.txt").write_text("x")
    p = SearchPresenter(LocalVFS(), tmp_path)
    assert len(p.search("foobar", mode=SearchMode.NAME_REGEX, case_sensitive=False)) == 1


def test_name_regex_case_sensitive(tmp_path):
    (tmp_path / "FooBar.txt").write_text("x")
    p = SearchPresenter(LocalVFS(), tmp_path)
    assert len(p.search("foobar", mode=SearchMode.NAME_REGEX, case_sensitive=True)) == 0


def test_content_regex_case_insensitive(tmp_path):
    p = _presenter(tmp_path, "Hello WORLD")
    assert len(p.search("hello", mode=SearchMode.CONTENT_REGEX, case_sensitive=False)) == 1


def test_content_regex_case_sensitive(tmp_path):
    p = _presenter(tmp_path, "Hello WORLD")
    assert len(p.search("hello", mode=SearchMode.CONTENT_REGEX, case_sensitive=True)) == 0


def test_content_regex_whole_word(tmp_path):
    p = _presenter(tmp_path, "foobar baz")
    assert len(p.search("foo", mode=SearchMode.CONTENT_REGEX, whole_word=True)) == 0
    p2 = _presenter(tmp_path, "foo baz")
    assert len(p2.search("foo", mode=SearchMode.CONTENT_REGEX, whole_word=True)) == 1
