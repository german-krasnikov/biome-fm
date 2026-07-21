"""TDD: BatchExecCmd and expand_template."""
from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import patch, call

import pytest

from biome_fm.commands.batch_exec_cmd import BatchExecCmd, expand_template


PHOTO = Path("/home/user/photo.jpg")
PATHS = [Path(f"/tmp/file{i}.txt") for i in range(3)]


def _cmd(template: str = "echo {f}", paths: list[Path] | None = None, cancel: threading.Event | None = None):
    return BatchExecCmd(template, paths or PATHS, cancel=cancel)


def test_expand_template_all_tokens():
    result = expand_template("cp {f} {d}/{n}_bak.{e}", PHOTO)
    assert result == "cp /home/user/photo.jpg /home/user/photo_bak.jpg"


def test_expand_template_no_tokens():
    assert expand_template("echo hello", PHOTO) == "echo hello"


def test_expand_template_extension_no_dot():
    assert expand_template("{e}", PHOTO) == "jpg"


def test_batch_exec_runs_subprocess():
    with patch("biome_fm.commands.batch_exec_cmd.subprocess.run") as mock_run:
        _cmd().execute()
    assert mock_run.call_count == 3


def test_batch_exec_cancel_stops():
    cancel = threading.Event()
    cancel.set()
    with patch("biome_fm.commands.batch_exec_cmd.subprocess.run") as mock_run:
        _cmd(cancel=cancel).execute()
    mock_run.assert_not_called()


def test_batch_exec_not_undoable():
    assert _cmd().undoable is False


def test_batch_exec_description():
    cmd = BatchExecCmd("echo {f}", PATHS)
    assert "echo {f}" in cmd.description
    assert "3" in cmd.description
