"""Tests for launch_external_diff."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, call

import pytest

from biome_fm.presenters.compare_presenter import launch_external_diff

LEFT = Path("/tmp/a.txt")
RIGHT = Path("/tmp/b.txt")


def test_launch_external_diff_calls_popen():
    with patch("subprocess.Popen") as mock_popen:
        launch_external_diff(LEFT, RIGHT, tool="meld")
    mock_popen.assert_called_once_with(["meld", str(LEFT), str(RIGHT)])


def test_configured_tool_used():
    with patch("subprocess.Popen") as mock_popen:
        launch_external_diff(LEFT, RIGHT, tool="vimdiff")
    mock_popen.assert_called_once_with(["vimdiff", str(LEFT), str(RIGHT)])


def test_default_tool_fallback_chain():
    """First candidate fails, second succeeds."""
    calls = []

    def fake_popen(args, **_kw):
        calls.append(args[0])
        if args[0] == "code":
            raise FileNotFoundError
        return object()

    with patch("subprocess.Popen", side_effect=fake_popen):
        launch_external_diff(LEFT, RIGHT)

    assert calls == ["code", "meld"]


def test_tool_with_flags_is_split():
    """tool='code --diff' must expand to ['code', '--diff', left, right]."""
    with patch("subprocess.Popen") as mock_popen:
        launch_external_diff(LEFT, RIGHT, tool="code --diff")
    mock_popen.assert_called_once_with(["code", "--diff", str(LEFT), str(RIGHT)])


def test_tool_not_found_raises():
    with patch("subprocess.Popen", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="No diff tool found"):
            launch_external_diff(LEFT, RIGHT)
