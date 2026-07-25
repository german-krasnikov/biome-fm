"""Unit tests for _workspace_mgmt — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._workspace_mgmt import (
    create_repo,
    create_workspace,
    delete_repo,
    delete_workspace,
    list_repos,
    list_workspaces,
    parse_repos,
    parse_workspaces,
)


def test_parse_workspaces_basic():
    out = "my_wk|/home/dev/wk|localhost:8087\n"
    items = parse_workspaces(out)
    assert len(items) == 1
    assert items[0].name == "my_wk"
    assert items[0].path == Path("/home/dev/wk")
    assert items[0].server == "localhost:8087"


def test_parse_workspaces_multiple():
    out = "wk1|/a|srv1\nwk2|/b|srv2\n"
    items = parse_workspaces(out)
    assert len(items) == 2
    assert items[1].name == "wk2"


def test_parse_workspaces_empty():
    assert parse_workspaces("") == []
    assert parse_workspaces("   \n  ") == []


def test_list_workspaces_parses_output(tmp_path):
    out = "my_wk|/home/dev/wk|localhost:8087\n"
    with patch("biome_fm.plastic._workspace_mgmt.run_cm", return_value=out):
        items = list_workspaces(tmp_path)
    assert items[0].name == "my_wk"
    assert items[0].server == "localhost:8087"


def test_create_workspace_calls_cm(tmp_path):
    with patch("biome_fm.plastic._workspace_mgmt.run_cm") as m:
        create_workspace("wk", "/path", "srv:8087", "repo", tmp_path)
    args = m.call_args[0][0]
    assert "workspace" in args
    assert "create" in args


def test_delete_workspace_calls_cm(tmp_path):
    with patch("biome_fm.plastic._workspace_mgmt.run_cm") as m:
        delete_workspace("wk", tmp_path)
    args = m.call_args[0][0]
    assert "workspace" in args
    assert "delete" in args
    assert "wk" in args


def test_parse_repos_basic():
    out = "MyRepo|localhost:8087\n"
    items = parse_repos(out)
    assert len(items) == 1
    assert items[0].name == "MyRepo"
    assert items[0].server == "localhost:8087"


def test_parse_repos_empty():
    assert parse_repos("") == []


def test_list_repos_parses_output(tmp_path):
    out = "MyRepo|localhost:8087\n"
    with patch("biome_fm.plastic._workspace_mgmt.run_cm", return_value=out):
        items = list_repos(tmp_path)
    assert items[0].name == "MyRepo"
    assert items[0].server == "localhost:8087"


def test_create_repo_calls_cm(tmp_path):
    with patch("biome_fm.plastic._workspace_mgmt.run_cm") as m:
        create_repo("repo1", tmp_path)
    args = m.call_args[0][0]
    assert "repo" in args
    assert "create" in args
    assert "repo1" in args


def test_delete_repo_calls_cm(tmp_path):
    with patch("biome_fm.plastic._workspace_mgmt.run_cm") as m:
        delete_repo("repo1", tmp_path)
    args = m.call_args[0][0]
    assert "repo" in args
    assert "delete" in args
    assert "repo1" in args
