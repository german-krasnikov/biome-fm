"""Unit tests for plastic._annotate — no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._annotate import get_blame, parse_blame

SAMPLE = (
    "1|alice|42|07/24/2026 10:00:00|def foo():\n"
    "2|bob|43|07/24/2026 11:00:00|    pass"
)
PIPE_SAMPLE = "3|carol|44|07/24/2026 12:00:00|x = a|b  # pipe in content"


def test_parse_blame_basic():
    lines = parse_blame(SAMPLE)
    assert len(lines) == 2
    assert lines[0].line_no == 1
    assert lines[0].owner == "alice"
    assert lines[0].content == "def foo():"
    assert lines[1].cs_id == 43


def test_parse_blame_pipe_in_content():
    lines = parse_blame(PIPE_SAMPLE)
    assert len(lines) == 1
    assert lines[0].content == "x = a|b  # pipe in content"


def test_parse_blame_skips_malformed():
    assert parse_blame("bad") == []


def test_parse_blame_skips_empty():
    assert parse_blame("") == []


def test_parse_blame_date_parsed():
    lines = parse_blame(SAMPLE)
    assert lines[0].date.year == 2026


def test_get_blame_calls_cm(tmp_path):
    with patch("biome_fm.plastic._annotate.run_cm", return_value=SAMPLE) as m:
        lines = get_blame(Path("file.py"), tmp_path)
    m.assert_called_once()
    assert "annotate" in m.call_args[0][0]
    assert len(lines) == 2
