"""Unit tests for _shelve.py."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._shelve import (
    delete_shelve,
    get_shelves,
    parse_shelves,
    shelve,
    unshelve,
)

# ── parse_shelves — standard ──────────────────────────────────────────────────

_STANDARD = "7|07/24/2026 14:00:00|alice|WIP shelve\n"


def test_parse_standard_line():
    result = parse_shelves(_STANDARD)
    assert len(result) == 1
    s = result[0]
    assert s.shelve_id == 7
    assert s.owner == "alice"
    assert s.comment == "WIP shelve"
    assert s.date == datetime(2026, 7, 24, 14, 0, 0)


def test_parse_empty_output():
    assert parse_shelves("") == []


def test_parse_skips_blank_lines():
    out = "\n\n7|07/24/2026 00:00:00|dev|msg\n\n"
    assert len(parse_shelves(out)) == 1


def test_parse_skips_non_int_id():
    assert parse_shelves("abc|07/24/2026 00:00:00|dev|msg\n") == []


def test_parse_skips_lines_fewer_than_four_parts():
    assert parse_shelves("7|date|owner\n") == []


def test_parse_pipe_in_comment_preserved():
    out = "3|07/24/2026 00:00:00|dev|fix: a|b|c\n"
    s = parse_shelves(out)[0]
    assert s.comment == "fix: a|b|c"


def test_parse_multiple_shelves():
    out = (
        "1|07/01/2026 10:00:00|bob|first\n"
        "2|07/02/2026 11:00:00|alice|second\n"
    )
    result = parse_shelves(out)
    assert [s.shelve_id for s in result] == [1, 2]


def test_parse_strips_whitespace():
    s = parse_shelves(" 5 | 07/24/2026 00:00:00 | alice | trimmed \n")[0]
    assert s.shelve_id == 5
    assert s.owner == "alice"
    assert s.comment == "trimmed"


# ── shelve ────────────────────────────────────────────────────────────────────

def test_shelve_basic(tmp_path):
    with patch("biome_fm.plastic._shelve.run_cm") as m:
        shelve("WIP", tmp_path)
    m.assert_called_once_with(["shelveset", "create", "-c=WIP"], cwd=tmp_path)


def test_shelve_with_paths(tmp_path):
    f1, f2 = tmp_path / "a.py", tmp_path / "b.py"
    with patch("biome_fm.plastic._shelve.run_cm") as m:
        shelve("msg", tmp_path, paths=[f1, f2])
    m.assert_called_once_with(
        ["shelveset", "create", "-c=msg", str(f1), str(f2)], cwd=tmp_path
    )


def test_shelve_no_paths_arg_omitted(tmp_path):
    with patch("biome_fm.plastic._shelve.run_cm") as m:
        shelve("msg", tmp_path, paths=None)
    args = m.call_args.args[0]
    assert "shelveset" in args
    # no extra path args beyond -c=msg
    assert len(args) == 3


# ── unshelve ──────────────────────────────────────────────────────────────────

def test_unshelve_correct_args(tmp_path):
    with patch("biome_fm.plastic._shelve.run_cm") as m:
        unshelve(42, tmp_path)
    m.assert_called_once_with(["shelveset", "apply", "42"], cwd=tmp_path)


# ── delete_shelve ─────────────────────────────────────────────────────────────

def test_delete_shelve_correct_args(tmp_path):
    with patch("biome_fm.plastic._shelve.run_cm") as m:
        delete_shelve(99, tmp_path)
    m.assert_called_once_with(["shelveset", "delete", "99"], cwd=tmp_path)


# ── get_shelves ───────────────────────────────────────────────────────────────

def test_get_shelves_calls_find_shelves(tmp_path):
    with patch("biome_fm.plastic._shelve.run_cm", return_value="") as m:
        get_shelves(tmp_path)
    args = m.call_args.args[0]
    assert args[0] == "find"
    assert args[1] == "shelves"
    assert any("--format=" in a for a in args)


def test_get_shelves_returns_parsed(tmp_path):
    out = "1|07/24/2026 00:00:00|dev|shelve one\n"
    with patch("biome_fm.plastic._shelve.run_cm", return_value=out):
        result = get_shelves(tmp_path)
    assert len(result) == 1
    assert result[0].shelve_id == 1


def test_get_shelves_empty_on_cm_error(tmp_path):
    with patch("biome_fm.plastic._shelve.run_cm", return_value=""):
        assert get_shelves(tmp_path) == []


# ── C49: -c= flag ────────────────────────────────────────────────────────────

def test_shelve_uses_dash_c_equals(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("biome_fm.plastic._shelve.run_cm",
                        lambda a, **kw: calls.append(a))
    shelve("wip", tmp_path)
    assert calls[0][2] == "-c=wip"  # fails today: calls[0][2] == "-m"
