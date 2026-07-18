"""Unit tests for GitStatusWorker HEAD mtime polling."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.git.status_cache import GitStatusCache
from biome_fm.git.worker import GitStatusWorker


def _make_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Create a minimal fake git repo. Returns (repo_root, head_path)."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    head = git_dir / "HEAD"
    head.write_text("ref: refs/heads/main\n")
    return tmp_path, head


def _worker(tmp_path: Path) -> GitStatusWorker:
    cache = GitStatusCache()
    return GitStatusWorker(cache)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_head_change_triggers_refresh(qtbot, tmp_path):
    """Modifying .git/HEAD mtime causes _check_head to re-submit a fetch."""
    repo, head = _make_repo(tmp_path)
    w = _worker(tmp_path)

    with patch.object(w._pool, "submit") as mock_submit:
        w.request(repo)
        assert mock_submit.call_count == 1

        # Simulate HEAD changing (touch with new mtime)
        time.sleep(0.01)
        head.write_text("ref: refs/heads/feature\n")

        # First _check_head records mtime (no re-trigger yet if first call)
        # Second call after mtime change should re-trigger
        w._check_head()  # records initial mtime
        head.touch()     # bump mtime
        w._check_head()  # detects change → re-trigger

        assert mock_submit.call_count == 2

    w.stop()


def test_watcher_not_started_outside_git(qtbot, tmp_path):
    """For a non-git dir, _head_timer must NOT be active after request()."""
    # tmp_path has no .git — find_repo returns None
    w = _worker(tmp_path)
    w.request(tmp_path)
    assert not w._head_timer.isActive()
    w.stop()


def test_watcher_stops_on_shutdown(qtbot, tmp_path):
    """stop() deactivates _head_timer."""
    repo, _ = _make_repo(tmp_path)
    w = _worker(tmp_path)
    with patch.object(w._pool, "submit"):
        w.request(repo)
    assert w._head_timer.isActive()
    w.stop()
    assert not w._head_timer.isActive()


def test_head_timer_stops_when_leaving_git(qtbot, tmp_path):
    """Navigating from git to non-git dir must stop the HEAD timer."""
    git_dir = tmp_path / "repo"
    git_dir.mkdir()
    repo, _ = _make_repo(git_dir)
    non_git = tmp_path / "elsewhere"
    non_git.mkdir()
    w = _worker(tmp_path)
    with patch.object(w._pool, "submit"):
        w.request(repo)
    assert w._head_timer.isActive()
    w.request(non_git)
    assert not w._head_timer.isActive()
    w.stop()


def test_same_mtime_no_refresh(qtbot, tmp_path):
    """Unchanged HEAD mtime → no extra submit beyond the initial request."""
    repo, _ = _make_repo(tmp_path)
    w = _worker(tmp_path)

    with patch.object(w._pool, "submit") as mock_submit:
        w.request(repo)
        w._check_head()  # record mtime
        w._check_head()  # same mtime → no re-trigger
        assert mock_submit.call_count == 1

    w.stop()
