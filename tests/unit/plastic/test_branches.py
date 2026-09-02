"""Unit tests for _branches.py — parse_branches(), switch_branch(), switch_changeset()."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

from biome_fm.plastic._branches import (
    delete_branch,
    get_branches,
    parse_branches,
    rename_branch,
    switch_branch,
    switch_changeset,
)

# ── parse_branches ────────────────────────────────────────────────────────────

def test_parse_standard_line():
    out = "/main|07/24/2026 12:00:00|alice\n"
    result = parse_branches(out)
    assert len(result) == 1
    b = result[0]
    assert b.name == "/main"
    assert b.owner == "alice"
    assert b.date == datetime(2026, 7, 24, 12, 0, 0)


def test_parse_multiple_branches():
    out = "/main|2026-01-01 00:00:00|alice\n/task-1|2026-01-02 00:00:00|bob\n"
    result = parse_branches(out)
    assert [b.name for b in result] == ["/main", "/task-1"]


def test_parse_branch_name_with_spaces():
    # Branch name may contain spaces; split is capped at 2 so name is intact
    out = "/main/my feature branch|2026-01-01 00:00:00|dev\n"
    b = parse_branches(out)[0]
    assert b.name == "/main/my feature branch"


def test_parse_strips_whitespace():
    out = " /main | 2026-01-01 00:00:00 | alice \n"
    b = parse_branches(out)[0]
    assert b.name == "/main"
    assert b.owner == "alice"


def test_parse_skips_fewer_than_three_parts():
    out = "/main|2026-01-01 00:00:00\n"  # only 2 parts
    assert parse_branches(out) == []


def test_parse_empty_output():
    assert parse_branches("") == []


def test_parse_skips_blank_lines():
    out = "\n/main|2026-01-01 00:00:00|alice\n\n"
    assert len(parse_branches(out)) == 1


# ── get_branches ──────────────────────────────────────────────────────────────

def test_get_branches_calls_run_cm(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm", return_value="") as m:
        get_branches(tmp_path)
    args = m.call_args.args[0]
    assert "find" in args
    assert "branches" in args


# ── switch_branch ─────────────────────────────────────────────────────────────

def test_switch_branch_adds_br_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        switch_branch("main", tmp_path)
    m.assert_called_once_with(["switch", "br:main"], cwd=tmp_path, timeout=None)


def test_switch_branch_passes_through_existing_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        switch_branch("br:/main/task-1", tmp_path)
    m.assert_called_once_with(["switch", "br:/main/task-1"], cwd=tmp_path, timeout=None)


# ── switch_changeset ──────────────────────────────────────────────────────────

def test_switch_changeset_uses_cs_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        switch_changeset(99, tmp_path)
    m.assert_called_once_with(["switch", "cs:99"], cwd=tmp_path, timeout=None)


# ── delete_branch ─────────────────────────────────────────────────────────────

def test_delete_branch_adds_br_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        delete_branch("/main/task-1", tmp_path)
    m.assert_called_once_with(["branch", "delete", "br:/main/task-1"], cwd=tmp_path, timeout=None)


def test_delete_branch_preserves_existing_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        delete_branch("br:/main", tmp_path)
    m.assert_called_once_with(["branch", "delete", "br:/main"], cwd=tmp_path, timeout=None)


# ── rename_branch ─────────────────────────────────────────────────────────────

def test_rename_branch_adds_br_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        rename_branch("/main/old", "new-name", tmp_path)
    m.assert_called_once_with(["branch", "rename", "br:/main/old", "new-name"], cwd=tmp_path, timeout=None)


def test_rename_branch_preserves_existing_prefix(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        rename_branch("br:/main/old", "new-name", tmp_path)
    m.assert_called_once_with(["branch", "rename", "br:/main/old", "new-name"], cwd=tmp_path, timeout=None)


# ── parent field ──────────────────────────────────────────────────────────────

def test_parse_branches_with_parent():
    out = "/main/task-1|/main|07/24/2026 12:00:00|alice\n"
    b = parse_branches(out)[0]
    assert b.name == "/main/task-1"
    assert b.parent == "/main"
    assert b.owner == "alice"


def test_parse_branches_backward_compat_three_fields():
    out = "/main|07/24/2026 12:00:00|alice\n"
    b = parse_branches(out)[0]
    assert b.parent == ""


# ── C50: mutating wrappers must pass timeout=None ─────────────────────────────

def test_switch_branch_uses_no_timeout(tmp_path):
    with patch("biome_fm.plastic._branches.run_cm") as m:
        switch_branch("main", tmp_path)
    kwargs = m.call_args_list[0].kwargs
    assert "timeout" in kwargs, "timeout kwarg must be explicitly passed"
    assert kwargs["timeout"] is None
