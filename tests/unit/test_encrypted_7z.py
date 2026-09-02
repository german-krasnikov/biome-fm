"""Tests for Encrypted7zCmd — AES-256 encrypted archive creation."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.commands.archive_cmd import Encrypted7zCmd


def _mock_run(returncode: int = 0, stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stderr = stderr
    return m


@patch("biome_fm.commands.archive_cmd.subprocess.run")
@patch("biome_fm.commands.archive_cmd.shutil.which", return_value="/usr/bin/7z")
def test_execute_calls_7z_with_correct_args(mock_which, mock_run):
    mock_run.return_value = _mock_run()
    sources = [Path("/tmp/a.txt"), Path("/tmp/b.txt")]
    archive = Path("/tmp/out.7z")

    Encrypted7zCmd(sources, archive, "secret").execute()

    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    cmd = call_kwargs[0][0]
    assert cmd[0] == "/usr/bin/7z"
    assert cmd[1] == "a"
    assert "-p" in cmd
    assert "-psecret" not in cmd  # password must NOT appear in argv
    assert "-mhe=on" in cmd
    assert str(archive) in cmd
    assert "/tmp/a.txt" in cmd
    assert "/tmp/b.txt" in cmd
    # password passed via stdin
    assert call_kwargs[1]["input"] == "secret\nsecret\n"
    assert call_kwargs[1]["timeout"] == 300


@patch("biome_fm.commands.archive_cmd.subprocess.run")
@patch("biome_fm.commands.archive_cmd.shutil.which", return_value="/usr/bin/7z")
def test_execute_raises_on_failure(mock_which, mock_run):
    mock_run.return_value = _mock_run(returncode=1, stderr="bad error")

    with pytest.raises(RuntimeError, match="7z failed"):
        Encrypted7zCmd([Path("/tmp/a.txt")], Path("/tmp/out.7z"), "pw").execute()


@patch("biome_fm.commands.archive_cmd.subprocess.run")
@patch("biome_fm.commands.archive_cmd.shutil.which", return_value="/usr/bin/7z")
def test_execute_handles_timeout(mock_which, mock_run, tmp_path):
    archive = tmp_path / "out.7z"
    archive.touch()
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="7z", timeout=300)

    with pytest.raises(RuntimeError, match="timed out"):
        Encrypted7zCmd([Path("/tmp/a.txt")], archive, "pw").execute()

    assert not archive.exists()  # unlink called on timeout


@patch("biome_fm.commands.archive_cmd.shutil.which", return_value=None)
def test_execute_raises_when_7z_missing(mock_which):
    with pytest.raises(RuntimeError, match="7z binary not found"):
        Encrypted7zCmd([Path("/tmp/a.txt")], Path("/tmp/out.7z"), "pw").execute()


def test_description():
    cmd = Encrypted7zCmd([], Path("/tmp/secret.7z"), "pw")
    assert cmd.description == "Encrypted archive secret.7z"


@patch("biome_fm.commands.archive_cmd.subprocess.run")
@patch("biome_fm.commands.archive_cmd.shutil.which", return_value="/usr/bin/7z")
def test_encrypted7z_timeout_unlinks_archive(mock_which, mock_run, tmp_path):
    """REGRESSION GUARD: TimeoutExpired causes archive unlink without calling undo()."""
    archive = tmp_path / "out.7z"
    archive.touch()
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="7z", timeout=300)

    cmd = Encrypted7zCmd([Path("/tmp/a.txt")], archive, "pw")
    with pytest.raises(RuntimeError, match="timed out"):
        cmd.execute()

    assert not archive.exists()
