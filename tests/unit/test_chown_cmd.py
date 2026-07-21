"""Unit tests for ChownCmd (F449)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from biome_fm.commands.chown_cmd import ChownCmd


def _stat(uid: int, gid: int) -> MagicMock:
    s = MagicMock()
    s.st_uid = uid
    s.st_gid = gid
    return s


def test_execute_changes_owner(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.touch()
    with patch("os.chown") as mock_chown, patch.object(Path, "stat", return_value=_stat(1000, 1000)):
        cmd = ChownCmd([f], uid=42, gid=99)
        cmd.execute()
    mock_chown.assert_called_once_with(f, 42, 99)


def test_undo_restores_owner(tmp_path: Path) -> None:
    f = tmp_path / "b.txt"
    f.touch()
    with patch("os.chown") as mock_chown, patch.object(Path, "stat", return_value=_stat(1000, 2000)):
        cmd = ChownCmd([f], uid=42, gid=99)
        cmd.execute()
        cmd.undo()
    assert mock_chown.call_args_list == [call(f, 42, 99), call(f, 1000, 2000)]


def test_windows_raises(tmp_path: Path) -> None:
    f = tmp_path / "c.txt"
    f.touch()
    with patch.object(sys, "platform", "win32"):
        cmd = ChownCmd([f], uid=0, gid=0)
        with pytest.raises(NotImplementedError):
            cmd.execute()


def test_description() -> None:
    cmd = ChownCmd([Path("x")], uid=42, gid=99)
    assert cmd.description == "chown 42:99 on 1 file(s)"


def test_multiple_files(tmp_path: Path) -> None:
    files = [tmp_path / f"f{i}" for i in range(3)]
    for f in files:
        f.touch()
    with patch("os.chown") as mock_chown, patch.object(Path, "stat", return_value=_stat(500, 500)):
        cmd = ChownCmd(files, uid=0, gid=0)
        cmd.execute()
    assert mock_chown.call_count == 3


def test_negative_one_passthrough(tmp_path: Path) -> None:
    """uid/gid -1 means 'keep current' — just forward to os.chown as-is."""
    f = tmp_path / "d.txt"
    f.touch()
    with patch("os.chown") as mock_chown, patch.object(Path, "stat", return_value=_stat(1000, 1000)):
        cmd = ChownCmd([f], uid=-1, gid=-1)
        cmd.execute()
    mock_chown.assert_called_once_with(f, -1, -1)
