"""Unit tests for highlight_rules — pure Python, no Qt."""
from biome_fm.models.highlight_rules import HighlightRule, match_highlight


def _rules(*args):
    """_rules("*.log", "#color") → [HighlightRule("*.log", "#color")]"""
    return [HighlightRule(p, c) for p, c in zip(args[::2], args[1::2])]


def test_glob_match():
    assert match_highlight("error.log", _rules("*.log", "#888888")) == "#888888"


def test_no_match():
    assert match_highlight("readme.md", _rules("*.log", "#888888")) is None


def test_first_wins():
    rules = _rules("*.log", "#aaaaaa") + _rules("error.*", "#bbbbbb")
    assert match_highlight("error.log", rules) == "#aaaaaa"


def test_empty_rules():
    assert match_highlight("error.log", []) is None


def test_case_insensitive():
    assert match_highlight("error.LOG", _rules("*.log", "#888888")) == "#888888"
