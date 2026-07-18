"""F250 — Conditional File Highlighting (Age/Size Rules)."""
from biome_fm.models.highlight_rules import HighlightRule, match_highlight


def test_match_highlight_returns_color():
    rules = [HighlightRule(pattern="*.log", color="#ff0000")]
    assert match_highlight("error.log", rules) == "#ff0000"


def test_no_rules_returns_none():
    assert match_highlight("error.log", []) is None
