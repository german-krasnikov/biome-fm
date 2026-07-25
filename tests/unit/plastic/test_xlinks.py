"""Unit tests for _xlinks.py — parse_xlinks pure-string parser."""
from __future__ import annotations

from biome_fm.plastic._xlinks import parse_xlinks
from biome_fm.plastic._models import Xlink


def test_parse_xlinks_empty():
    assert parse_xlinks("") == []


def test_parse_xlinks_line():
    out = "libs/engine|server1|MyRepo|/main|42\n"
    result = parse_xlinks(out)
    assert len(result) == 1
    assert result[0] == Xlink("libs/engine", "server1", "MyRepo", "/main", 42)


def test_parse_xlinks_no_cs():
    out = "libs/ui|server2|UiRepo|/dev|\n"
    result = parse_xlinks(out)
    assert result[0].cs_id == 0


def test_parse_xlinks_minimal():
    out = "libs/x|srv|repo\n"
    result = parse_xlinks(out)
    assert result[0] == Xlink("libs/x", "srv", "repo", "", 0)
