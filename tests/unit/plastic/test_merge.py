"""Unit tests for _merge.py — merge_branch(), merge_changeset()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._cm import CMError
from biome_fm.plastic._merge import merge_branch, merge_changeset


def test_merge_branch_adds_br_prefix(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="merged") as m:
        result = merge_branch("task-1", tmp_path)
    m.assert_called_once_with(["merge", "br:task-1"], cwd=tmp_path, timeout=60, safe=False)
    assert result == "merged"


def test_merge_branch_passes_through_existing_prefix(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="ok") as m:
        merge_branch("br:/main/task-1", tmp_path)
    m.assert_called_once_with(["merge", "br:/main/task-1"], cwd=tmp_path, timeout=60, safe=False)


def test_merge_changeset_uses_cs_prefix(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="ok") as m:
        result = merge_changeset(42, tmp_path)
    m.assert_called_once_with(["merge", "cs:42"], cwd=tmp_path, timeout=60)
    assert result == "ok"


def test_merge_branch_raises_on_error(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", side_effect=CMError("conflict")):
        with pytest.raises(CMError, match="conflict"):
            merge_branch("main", tmp_path)


def test_merge_changeset_raises_on_error(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", side_effect=CMError("failed")):
        with pytest.raises(CMError, match="failed"):
            merge_changeset(99, tmp_path)


# ── Merge enhancements (4.9) ──────────────────────────────────────────────────

def test_merge_branch_preview_flag(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="preview") as m:
        merge_branch("main", tmp_path, preview=True)
    args = m.call_args.args[0]
    assert "--preview" in args


def test_merge_branch_keepsource(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="ok") as m:
        merge_branch("main", tmp_path, resolve="keepsource")
    args = m.call_args.args[0]
    assert "--keepsource" in args


def test_merge_changeset_cherrypick_flags(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="ok") as m:
        merge_changeset(10, tmp_path, cherrypick=True)
    args = m.call_args.args[0]
    assert "--merge" in args
    assert "--cherrypicking" in args


def test_merge_branch_preview_safe_true(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="preview") as m:
        merge_branch("main", tmp_path, preview=True)
    assert m.call_args.kwargs.get("safe") is True


# ── Semantic merge (#7) ───────────────────────────────────────────────────────

def test_merge_branch_semantic(tmp_path):
    with patch("biome_fm.plastic._merge.run_cm", return_value="") as m:
        merge_branch("feature", tmp_path, semantic=True)
    assert "--semantic" in m.call_args[0][0]
