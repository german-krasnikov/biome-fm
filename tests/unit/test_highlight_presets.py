"""TDD: highlight presets and expand_rules."""
from __future__ import annotations

import fnmatch

import pytest

from biome_fm.models.highlight_rules import (
    HIGHLIGHT_PRESETS,
    HighlightRule,
    expand_rules,
)


def test_presets_exist():
    assert set(HIGHLIGHT_PRESETS) >= {"default", "dark", "light"}


def test_default_preset_empty():
    assert HIGHLIGHT_PRESETS["default"] == []


def test_dark_preset_has_rules():
    assert len(HIGHLIGHT_PRESETS["dark"]) == 6


def test_expand_rules_splits_comma():
    rules = [{"pattern": "*.zip,*.tar", "color": "#aaaaaa"}]
    expanded = expand_rules(rules)
    assert len(expanded) == 2
    assert expanded[0].pattern == "*.zip"
    assert expanded[1].pattern == "*.tar"


def test_expand_rules_preserves_color():
    rules = [{"pattern": "*.py,*.js", "color": "#fcd34d"}]
    expanded = expand_rules(rules)
    assert all(r.color == "#fcd34d" for r in expanded)


def test_expand_rules_empty():
    assert expand_rules([]) == []


def test_match_after_expand():
    rules = expand_rules([{"pattern": "*.zip,*.tar", "color": "#aaaaaa"}])
    colors = {r.pattern: r.color for r in rules}
    assert fnmatch.fnmatch("archive.zip", "*.zip")
    assert rules[0].pattern == "*.zip"
