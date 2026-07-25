"""Unit tests for _lock.py — parse_locks(), lock(), unlock(), get_locks()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._lock import get_locks, lock, parse_locks, unlock
from biome_fm.plastic._models import Lock

# ── parse_locks — normal ──────────────────────────────────────────────────────

def test_parse_normal_line():
    out = "/workspace/foo.cs|alice|/main|Locked\n"
    result = parse_locks(out)
    assert result == [Lock(path=Path("/workspace/foo.cs"), owner="alice", branch="/main", status="Locked")]


def test_parse_multiple_lines():
    out = "/a.cs|alice|/main|Locked\n/b.cs|bob|/task-1|Locked\n"
    result = parse_locks(out)
    assert [r.owner for r in result] == ["alice", "bob"]
    assert [r.branch for r in result] == ["/main", "/task-1"]


def test_parse_strips_whitespace():
    out = " /a.cs | alice | /main | Locked \n"
    r = parse_locks(out)[0]
    assert r.path == Path("/a.cs")
    assert r.owner == "alice"
    assert r.branch == "/main"
    assert r.status == "Locked"


# ── parse_locks — edge cases ──────────────────────────────────────────────────

def test_parse_empty():
    assert parse_locks("") == []


def test_parse_skips_blank_lines():
    out = "\n\n/x.cs|dev|/main|Locked\n\n"
    assert len(parse_locks(out)) == 1


def test_parse_skips_malformed_no_delimiters():
    out = "nodelimiters\n/ok.cs|owner|/main|Locked\n"
    result = parse_locks(out)
    assert len(result) == 1
    assert result[0].owner == "owner"


def test_parse_skips_only_two_parts():
    out = "path|owner\n/ok.cs|alice|/main|Locked\n"
    result = parse_locks(out)
    assert len(result) == 1


def test_parse_retained_status():
    out = "/workspace/foo.cs|alice|/main|Retained\n"
    assert parse_locks(out)[0].status == "Retained"


def test_parse_three_field_fallback_defaults_locked():
    out = "/a.cs|owner|/main\n"
    assert parse_locks(out)[0].status == "Locked"


def test_parse_mixed_statuses():
    out = "/a.cs|alice|/main|Locked\n/b.cs|bob|/task|Retained\n"
    result = parse_locks(out)
    assert result[0].status == "Locked"
    assert result[1].status == "Retained"


# ── lock / unlock ──────────────────────────────────────────────────────────────

def test_lock_calls_cm_with_correct_args(tmp_path):
    target = tmp_path / "file.cs"
    with patch("biome_fm.plastic._lock.run_cm", side_effect=["/main\n", None]) as m:
        lock(target, tmp_path)
    wi_call, create_call = m.call_args_list
    assert wi_call[0][0] == ["wi", "--format={workspacebranch}"]
    assert create_call[0][0] == ["lock", "create", "br:/main", str(target)]


def test_lock_strips_branch_whitespace(tmp_path):
    target = tmp_path / "f.cs"
    with patch("biome_fm.plastic._lock.run_cm", side_effect=["  /main  \n", None]) as m:
        lock(target, tmp_path)
    assert m.call_args_list[1][0][0][2] == "br:/main"


def test_unlock_calls_cm_with_correct_args(tmp_path):
    target = tmp_path / "file.cs"
    with patch("biome_fm.plastic._lock.run_cm") as m:
        unlock(target, tmp_path)
    m.assert_called_once_with(["lock", "unlock", str(target)], cwd=tmp_path)


def test_lock_propagates_cm_error(tmp_path):
    from biome_fm.plastic._cm import CMError
    with patch("biome_fm.plastic._lock.run_cm", side_effect=CMError("fail")):
        with pytest.raises(CMError):
            lock(tmp_path / "f.cs", tmp_path)


# ── get_locks ──────────────────────────────────────────────────────────────────

def test_get_locks_calls_lock_list_machinereadable(tmp_path):
    with patch("biome_fm.plastic._lock.run_cm", return_value="") as m:
        get_locks(tmp_path)
    m.assert_called_once_with(["lock", "list", "--machinereadable"], cwd=tmp_path, safe=True)


def test_get_locks_returns_parsed_locks(tmp_path):
    out = "/src/foo.cs|alice|/main\n/src/bar.cs|bob|/task\n"
    with patch("biome_fm.plastic._lock.run_cm", return_value=out):
        result = get_locks(tmp_path)
    assert len(result) == 2
    assert result[0].owner == "alice"
    assert result[1].branch == "/task"


def test_get_locks_empty_on_safe_failure(tmp_path):
    with patch("biome_fm.plastic._lock.run_cm", return_value=""):
        assert get_locks(tmp_path) == []


# ── Lock dataclass ─────────────────────────────────────────────────────────────

def test_lock_status_field():
    lk = Lock(path=Path("/a.cs"), owner="alice", branch="/main", status="Retained")
    assert lk.status == "Retained"


def test_lock_status_defaults_to_locked():
    lk = Lock(path=Path("/a.cs"), owner="alice", branch="/main")
    assert lk.status == "Locked"
