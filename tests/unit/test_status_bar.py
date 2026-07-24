"""TDD tests for status bar enhancements (Feature #8)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


def test_ops_counter_increments() -> None:
    from biome_fm.app import _OpsCounter
    results: list[int] = []
    counter = _OpsCounter(results.append)
    counter.inc()
    assert results[-1] == 1
    counter.inc()
    assert results[-1] == 2


def test_ops_counter_decrements() -> None:
    from biome_fm.app import _OpsCounter
    results: list[int] = []
    counter = _OpsCounter(results.append)
    counter.inc()
    counter.inc()
    counter.dec()
    assert results[-1] == 1


def test_ops_counter_clamps_at_zero() -> None:
    from biome_fm.app import _OpsCounter
    results: list[int] = []
    counter = _OpsCounter(results.append)
    counter.dec()  # should not go negative
    assert results[-1] == 0


def test_git_branch_displayed() -> None:
    from biome_fm.git.branch_ops import current_branch
    mock_result = MagicMock()
    mock_result.stdout = "main\n"
    with patch("biome_fm.git.run.subprocess.run", return_value=mock_result):
        branch = current_branch(Path("/some/repo"))
    assert branch == "main"


def test_git_branch_no_repo() -> None:
    from biome_fm.git.branch_ops import current_branch
    with patch("biome_fm.git.run.subprocess.run", side_effect=FileNotFoundError):
        branch = current_branch(Path("/tmp"))
    assert branch == ""
