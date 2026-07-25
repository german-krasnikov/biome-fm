"""Unit tests for plastic._history — no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._history import get_file_history, parse_history
from biome_fm.plastic._models import Revision

SAMPLE = (
    "42|07/24/2026 10:00:00|alice|/main|7|Fix bug\n"
    "99|07/25/2026 11:00:00|bob|/main/task|8|Add feat"
)


def test_parse_history_basic():
    revs = parse_history(SAMPLE)
    assert len(revs) == 2
    assert revs[0].cs_id == 42
    assert revs[0].owner == "alice"
    assert revs[0].rev_id == 7
    assert revs[1].branch == "/main/task"


def test_parse_history_comment():
    revs = parse_history(SAMPLE)
    assert revs[0].comment == "Fix bug"


def test_parse_history_date_parsed():
    revs = parse_history(SAMPLE)
    assert revs[0].date.year == 2026
    assert revs[0].date.month == 7


def test_parse_history_skips_malformed():
    assert parse_history("bad|line") == []


def test_parse_history_skips_empty_lines():
    assert parse_history("") == []


def test_get_file_history_calls_cm(tmp_path):
    with patch("biome_fm.plastic._history.run_cm", return_value=SAMPLE) as m:
        revs = get_file_history(Path("file.py"), tmp_path, limit=10)
    m.assert_called_once()
    args = m.call_args[0][0]
    assert "--limit=10" in args
    assert "history" in args
    assert len(revs) == 2


def test_get_file_history_default_limit(tmp_path):
    with patch("biome_fm.plastic._history.run_cm", return_value="") as m:
        get_file_history(Path("file.py"), tmp_path)
    args = m.call_args[0][0]
    assert "--limit=50" in args


def test_parse_history_pipe_in_comment():
    line = "42|07/24/2026 10:00:00|alice|/main|7|Fix a|b race"
    revs = parse_history(line)
    assert len(revs) == 1
    assert revs[0].comment == "Fix a|b race"
    assert revs[0].rev_id == 7
    assert revs[0].branch == "/main"
