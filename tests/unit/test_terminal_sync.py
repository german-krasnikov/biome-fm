"""Unit tests for OSC 7 parsing in terminal panel."""
from __future__ import annotations

import re

import pytest


def test_osc7_parsed():
    from biome_fm.views.terminal_panel import _OSC7_RE
    m = _OSC7_RE.search("\x1b]7;file://hostname/tmp/mydir\x07")
    assert m is not None
    assert m.group(1) == "/tmp/mydir"


def test_osc7_no_match_plain_text():
    from biome_fm.views.terminal_panel import _OSC7_RE
    assert _OSC7_RE.search("just regular output\n") is None


def test_extract_paths_from_osc7():
    """extract_osc7_paths returns all paths from output with OSC 7 sequences."""
    from biome_fm.views.terminal_panel import _OSC7_RE
    data = "some output\x1b]7;file://host/home/user/proj\x07more text"
    paths = [m.group(1) for m in _OSC7_RE.finditer(data)]
    assert paths == ["/home/user/proj"]
