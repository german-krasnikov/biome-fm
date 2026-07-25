"""Unit tests for _status.py — parse_status() and get_status()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch

import pytest

from biome_fm.plastic._status import get_status, parse_status

_CWD = Path("/workspace")


# ── parse_status — machinereadable format ─────────────────────────────────────

def test_machinereadable_absolute_path():
    items = parse_status("CO|/workspace/src/file.py\n", _CWD)
    assert len(items) == 1
    assert items[0].status == "CO"
    assert items[0].path == Path("/workspace/src/file.py")


def test_machinereadable_multiple_items():
    out = "CO|/w/a.py\nAD|/w/b.py\nPR|/w/c.py\n"
    items = parse_status(out, _CWD)
    assert [i.status for i in items] == ["CO", "AD", "PR"]


def test_machinereadable_path_with_spaces():
    items = parse_status("CH|/workspace/my file.py\n", _CWD)
    assert items[0].path == Path("/workspace/my file.py")


# ── parse_status — plain format ───────────────────────────────────────────────

def test_plain_format_relative_path_resolved_against_cwd():
    items = parse_status("CO  src/file.py\n", _CWD)
    assert items[0].path == (_CWD / "src/file.py").resolve()


def test_plain_format_leading_spaces_stripped():
    items = parse_status("  CH  /abs/path.py\n", _CWD)
    assert items[0].status == "CH"


def test_plain_format_absolute_path_kept():
    items = parse_status("AD  /abs/file.py\n", _CWD)
    assert items[0].path == Path("/abs/file.py")


# ── parse_status — code normalization ────────────────────────────────────────

def test_lowercase_code_normalized():
    items = parse_status("co|/w/a.py\n", _CWD)
    assert items[0].status == "CO"


# ── parse_status — filtering ──────────────────────────────────────────────────

def test_unknown_status_code_skipped():
    items = parse_status("ZZ|/w/a.py\nCO|/w/b.py\n", _CWD)
    assert len(items) == 1
    assert items[0].status == "CO"


def test_empty_lines_skipped():
    items = parse_status("\n\n\nCO|/w/a.py\n\n", _CWD)
    assert len(items) == 1


def test_single_token_line_skipped():
    items = parse_status("CO\n", _CWD)
    assert items == []


def test_empty_output_returns_empty_list():
    assert parse_status("", _CWD) == []


def test_pipe_only_line_skipped():
    # "|" alone → parts has empty strings, code "" not in _CODES
    items = parse_status("|\n", _CWD)
    assert items == []


# ── get_status — run_cm interaction ──────────────────────────────────────────

def test_get_status_uses_machinereadable_first(tmp_path):
    with patch("biome_fm.plastic._status.run_cm", return_value="CO|/w/a.py\n") as m:
        items = get_status(tmp_path)
    assert m.call_args_list[0] == call(
        ["status", "--all", "--machinereadable"], cwd=tmp_path, safe=True
    )
    assert len(items) == 1


def test_get_status_falls_back_to_plain_when_machinereadable_empty(tmp_path):
    returns = ["", "CO  /w/a.py\n"]
    with patch("biome_fm.plastic._status.run_cm", side_effect=returns) as m:
        items = get_status(tmp_path)
    assert m.call_count == 2
    assert m.call_args_list[1] == call(["status", "--all"], cwd=tmp_path, safe=True)
    assert len(items) == 1


def test_get_status_empty_workspace_returns_empty(tmp_path):
    with patch("biome_fm.plastic._status.run_cm", return_value=""):
        assert get_status(tmp_path) == []
