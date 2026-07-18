"""Tests for declarative opener rules (F098)."""
import tomllib
from pathlib import Path

import pytest

from biome_fm.models.opener_rules import OpenerRule, find_opener, load_rules


def test_pdf_rule_matched():
    rules = [OpenerRule(match="*.pdf", cmd="zathura {}")]
    assert find_opener(rules, "report.pdf") == "zathura {}"


def test_fallback_when_no_rule():
    rules = [OpenerRule(match="*.pdf", cmd="zathura {}")]
    assert find_opener(rules, "image.png") is None


def test_first_match_wins():
    rules = [
        OpenerRule(match="*.pdf", cmd="zathura {}"),
        OpenerRule(match="*.pdf", cmd="evince {}"),
    ]
    assert find_opener(rules, "doc.pdf") == "zathura {}"


def test_empty_rules():
    assert find_opener([], "anything.pdf") is None


def test_rule_round_trip(tmp_path: Path):
    toml_file = tmp_path / "rules.toml"
    toml_file.write_text('[[rule]]\nmatch = "*.pdf"\ncmd = "zathura {}"\n')
    rules = load_rules(toml_file)
    assert find_opener(rules, "doc.pdf") == "zathura {}"


def test_load_rules_missing_file(tmp_path: Path):
    assert load_rules(tmp_path / "nonexistent.toml") == []
