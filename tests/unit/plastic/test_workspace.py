"""Unit tests for _workspace.get_workspace_info — RED phase."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._workspace import get_workspace_info  # type: ignore[import]

_WI_OUTPUT = """\
Workspace name: MyWS@server:8087
Workspace path: /path/to/ws
Server: server:8087
Last changeset: 42 on /main@server:8087
Controlled: Yes
"""


def test_parse_workspace_info_full(tmp_path):
    with patch("biome_fm.plastic._workspace.run_cm", return_value=_WI_OUTPUT):
        wi = get_workspace_info(tmp_path)
    assert wi.name == "MyWS"
    assert wi.branch == "/main"
    assert wi.last_cs == 42
    assert wi.wk_path == tmp_path


def test_parse_workspace_info_server(tmp_path):
    with patch("biome_fm.plastic._workspace.run_cm", return_value=_WI_OUTPUT):
        wi = get_workspace_info(tmp_path)
    assert wi.server == "server:8087"


def test_parse_workspace_info_empty(tmp_path):
    with patch("biome_fm.plastic._workspace.run_cm", return_value=""):
        wi = get_workspace_info(tmp_path)
    assert wi.name == tmp_path.name
    assert wi.server == ""
    assert wi.branch == ""
    assert wi.last_cs == 0
    assert wi.wk_path == tmp_path


# Single-line "Branch /main@repo@server" format (some cm versions)
_WI_SINGLE_LINE = "Branch /main@ts_playable_12275@PLR_Worldwide_Sales_Limited@cloud\n"


def test_parse_workspace_info_single_line_branch(tmp_path):
    with patch("biome_fm.plastic._workspace.run_cm", return_value=_WI_SINGLE_LINE):
        wi = get_workspace_info(tmp_path)
    assert wi.branch == "/main"


def test_parse_workspace_info_single_line_repo_name(tmp_path):
    with patch("biome_fm.plastic._workspace.run_cm", return_value=_WI_SINGLE_LINE):
        wi = get_workspace_info(tmp_path)
    # repo name is second @-segment: ts_playable_12275
    assert wi.name == "ts_playable_12275"
