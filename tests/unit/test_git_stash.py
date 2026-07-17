"""Unit tests for Git Stash Manager."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_list_parsed():
    from biome_fm.views.git_stash_dialog import parse_stash_list
    raw = (
        "stash@{0}: On main: my feature\n"
        "stash@{1}: WIP on dev: abc1234 another thing\n"
    )
    items = parse_stash_list(raw)
    assert len(items) == 2
    assert items[0] == "stash@{0}: On main: my feature"
    assert items[1] == "stash@{1}: WIP on dev: abc1234 another thing"


def test_list_parsed_empty():
    from biome_fm.views.git_stash_dialog import parse_stash_list
    assert parse_stash_list("") == []
    assert parse_stash_list("   \n  ") == []


def test_presenter_refresh(tmp_path):
    (tmp_path / ".git").mkdir()
    from biome_fm.views.git_stash_dialog import GitStashDialog, GitStashPresenter
    view = MagicMock(spec=GitStashDialog)
    with patch("biome_fm.views.git_stash_dialog.run_git", return_value="stash@{0}: msg\n"):
        p = GitStashPresenter(view, tmp_path)
    view.set_items.assert_called_with(["stash@{0}: msg"])
