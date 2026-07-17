"""Unit tests for open_terminal platform function."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import biome_fm.utils.platform as plat


def test_platform_macos_command():
    """open_terminal launches 'open -a Terminal <dir>' on macOS."""
    with (
        patch.object(plat, "IS_MAC", True),
        patch.object(plat, "IS_WIN", False),
        patch("biome_fm.utils.platform.subprocess.Popen") as mock_popen,
        patch.object(Path, "is_dir", return_value=True),
    ):
        plat.open_terminal(Path("/Users/test/project"))
    args = mock_popen.call_args[0][0]
    assert args[:3] == ["open", "-a", "Terminal"]
    assert args[3] == "/Users/test/project"


def test_open_terminal_uses_parent_for_file():
    """open_terminal resolves to parent dir when given a file path."""
    with (
        patch.object(plat, "IS_MAC", True),
        patch.object(plat, "IS_WIN", False),
        patch("biome_fm.utils.platform.subprocess.Popen") as mock_popen,
        patch.object(Path, "is_dir", return_value=False),
    ):
        plat.open_terminal(Path("/Users/test/project/file.txt"))
    args = mock_popen.call_args[0][0]
    assert args[3] == "/Users/test/project"
