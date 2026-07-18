"""Tests for project action detection (F094)."""
from pathlib import Path

import pytest

from biome_fm.presenters.project_actions import ProjectAction, detect_actions


def test_python_project_actions(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").touch()
    labels = [a.label for a in detect_actions(tmp_path)]
    assert "Run Tests" in labels


def test_node_project_actions(tmp_path: Path) -> None:
    (tmp_path / "package.json").touch()
    labels = [a.label for a in detect_actions(tmp_path)]
    assert "Dev Server" in labels


def test_go_project_actions(tmp_path: Path) -> None:
    (tmp_path / "go.mod").touch()
    labels = [a.label for a in detect_actions(tmp_path)]
    assert "Build" in labels


def test_no_project_empty(tmp_path: Path) -> None:
    assert detect_actions(tmp_path) == []


def test_git_repo_has_commit(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    labels = [a.label for a in detect_actions(tmp_path)]
    assert "Git Commit" in labels
