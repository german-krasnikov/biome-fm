"""Unit tests for _changesets.py — parse_changesets(), get_changesets(), mutations."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import call, patch

import pytest

from biome_fm.plastic._changesets import (
    checkin,
    edit_comment,
    get_changesets,
    parse_changesets,
    rollback_changeset,
    undo,
    undo_all,
    undo_keep,
    update,
)
from biome_fm.plastic._cm import CMError

# ── parse_changesets — standard ───────────────────────────────────────────────

_STANDARD = "42|07/24/2026 14:00:00|alice|/main|Initial commit\n"


def test_parse_standard_line():
    result = parse_changesets(_STANDARD)
    assert len(result) == 1
    cs = result[0]
    assert cs.cs_id == 42
    assert cs.owner == "alice"
    assert cs.branch == "/main"
    assert cs.comment == "Initial commit"
    assert cs.date == datetime(2026, 7, 24, 14, 0, 0)


def test_parse_multiple_changesets():
    out = (
        "1|07/01/2026 10:00:00|bob|/main|first\n"
        "2|07/02/2026 11:00:00|alice|/task-1|second\n"
    )
    result = parse_changesets(out)
    assert [cs.cs_id for cs in result] == [1, 2]


def test_parse_strips_whitespace_from_fields():
    out = " 10 | 07/24/2026 14:00:00 | alice | /main | trimmed \n"
    cs = parse_changesets(out)[0]
    assert cs.cs_id == 10
    assert cs.owner == "alice"
    assert cs.branch == "/main"
    assert cs.comment == "trimmed"


# ── parse_changesets — pipe in comment ───────────────────────────────────────

def test_parse_pipe_in_comment_preserved():
    # comment = "fix: a|b|c" — only cap at 4 splits so the rest is comment
    out = "5|07/24/2026 00:00:00|dev|/main|fix: a|b|c\n"
    cs = parse_changesets(out)[0]
    assert cs.comment == "fix: a|b|c"


def test_parse_exactly_five_pipes_comment_empty():
    out = "5|07/24/2026 00:00:00|dev|/main|\n"
    cs = parse_changesets(out)[0]
    assert cs.comment == ""


# ── parse_changesets — malformed lines ───────────────────────────────────────

def test_parse_skips_non_int_cs_id():
    out = "abc|07/24/2026 00:00:00|dev|/main|msg\n"
    assert parse_changesets(out) == []


def test_parse_skips_lines_with_fewer_than_five_parts():
    out = "42|date|owner\n"  # only 3 parts after split(|,4)
    assert parse_changesets(out) == []


def test_parse_empty_output():
    assert parse_changesets("") == []


def test_parse_skips_blank_lines():
    out = "\n\n42|07/24/2026 00:00:00|a|/main|msg\n\n"
    assert len(parse_changesets(out)) == 1


# ── get_changesets — limit ────────────────────────────────────────────────────

def _make_output(n: int) -> str:
    return "\n".join(
        f"{i}|07/24/2026 00:00:00|dev|/main|cs {i}" for i in range(1, n + 1)
    ) + "\n"


def test_get_changesets_limit_slices_to_newest(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm", return_value=_make_output(20)):
        result = get_changesets(tmp_path, limit=5)
    assert len(result) == 5
    assert result[0].cs_id == 16  # last 5 of 1..20


def test_get_changesets_no_truncation_when_count_lte_limit(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm", return_value=_make_output(3)):
        result = get_changesets(tmp_path, limit=10)
    assert len(result) == 3


def test_get_changesets_zero_limit_returns_all(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm", return_value=_make_output(15)):
        result = get_changesets(tmp_path, limit=0)
    assert len(result) == 15


def test_get_changesets_calls_run_cm_with_format(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm", return_value="") as m:
        get_changesets(tmp_path)
    args = m.call_args.args[0]
    assert args[0] == "find"
    assert args[1] == "changesets"
    assert any("--format=" in a for a in args)


# ── Mutations ─────────────────────────────────────────────────────────────────

def test_checkin_passes_message(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        checkin("my commit", tmp_path)
    m.assert_called_once_with(["checkin", "-m", "my commit"], cwd=tmp_path)


def test_checkin_with_paths_passes_file_args(tmp_path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        checkin("msg", tmp_path, paths=[f1, f2])
    m.assert_called_once_with(
        ["checkin", "-m", "msg", str(f1), str(f2)], cwd=tmp_path
    )


def test_update_calls_update(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        update(tmp_path)
    m.assert_called_once_with(["update"], cwd=tmp_path)


def test_undo_passes_path(tmp_path):
    target = tmp_path / "src" / "file.py"
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        undo(target, tmp_path)
    m.assert_called_once_with(["undo", str(target)], cwd=tmp_path)


def test_rollback_changeset(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        rollback_changeset(99, tmp_path)
    m.assert_called_once_with(["undo", "--changeset=cs:99"], cwd=tmp_path)


def test_rollback_changeset_error(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm", side_effect=CMError("fail")):
        with pytest.raises(CMError):
            rollback_changeset(99, tmp_path)


# ── edit_comment (4.10) ───────────────────────────────────────────────────────

def test_edit_comment_calls_cm_changeset_editcomment(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        edit_comment(42, "new msg", tmp_path)
    m.assert_called_once_with(
        ["changeset", "editcomment", "cs:42", "new msg"], cwd=tmp_path
    )


# ── Undo variants (#10) ───────────────────────────────────────────────────────

def test_undo_all_calls_cm(tmp_path):
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        undo_all(tmp_path)
    assert m.call_args[0][0] == ["undo", "--all"]


def test_undo_keep_calls_cm(tmp_path):
    f = tmp_path / "a.py"
    with patch("biome_fm.plastic._changesets.run_cm") as m:
        undo_keep(f, tmp_path)
    assert "--keep" in m.call_args[0][0]
