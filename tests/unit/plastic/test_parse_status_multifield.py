"""Unit tests for parse_status() with real cm --machinereadable multi-field output."""
from __future__ import annotations

from pathlib import Path

from biome_fm.plastic._status import parse_status

_CWD = Path("/workspace")


def test_multifield_format_two_items():
    out = "CH|/path/to/file.txt|False|NO_MERGES\nAD|/path/new.txt|True|NO_MERGES"
    items = parse_status(out, _CWD)
    assert len(items) == 2


def test_multifield_path_no_junk():
    out = "CH|/path/to/file.txt|False|NO_MERGES"
    items = parse_status(out, _CWD)
    assert items[0].path == Path("/path/to/file.txt")
    assert "False" not in str(items[0].path)
    assert "NO_MERGES" not in str(items[0].path)


def test_multifield_statuses_correct():
    out = "CH|/a.py|False|NO_MERGES\nAD|/b.py|True|NO_MERGES"
    items = parse_status(out, _CWD)
    assert items[0].status == "CH"
    assert items[1].status == "AD"


def test_plain_space_format_strips_trailing_metadata():
    """cm on some versions outputs space-separated with trailing True/False NO_MERGES."""
    out = (
        "STATUS 70 ts_playable_12275 PLR_Worldwide_Sales_Limited@cloud\n"
        "CH /Users/user/workspace/file.asset False NO_MERGES\n"
        "PR /Users/user/workspace/script.cs False NO_MERGES\n"
    )
    items = parse_status(out, _CWD)
    assert len(items) == 2
    assert str(items[0].path) == "/Users/user/workspace/file.asset"
    assert "False" not in str(items[0].path)
    assert "NO_MERGES" not in str(items[0].path)
    assert str(items[1].path) == "/Users/user/workspace/script.cs"
