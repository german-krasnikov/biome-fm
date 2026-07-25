"""Unit tests for _git_sync — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._git_sync import git_sync_status, sync_git


def test_sync_git_calls_cm(tmp_path):
    with patch("biome_fm.plastic._git_sync.run_cm", return_value="synced") as m:
        result = sync_git("https://github.com/org/repo.git", tmp_path)
    assert result == "synced"
    args = m.call_args[0][0]
    assert "git" in args
    assert "https://github.com/org/repo.git" in args


def test_sync_git_passes_timeout(tmp_path):
    with patch("biome_fm.plastic._git_sync.run_cm") as m:
        m.return_value = ""
        sync_git("https://github.com/org/repo.git", tmp_path)
    assert m.call_args[1].get("timeout") == 300


def test_git_sync_status_calls_cm(tmp_path):
    with patch("biome_fm.plastic._git_sync.run_cm", return_value="no sync") as m:
        result = git_sync_status(tmp_path)
    assert result == "no sync"
    args = m.call_args[0][0]
    assert "--status" in args
