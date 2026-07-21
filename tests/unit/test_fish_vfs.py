"""TDD tests for FISH VFS (Files over Shell)."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock

import pytest


# -- _parse_ls_line tests (pure, no mocks needed) ----------------------------

def test_parse_ls_line_dir():
    from biome_fm.models.fish_vfs import _parse_ls_line
    info = _parse_ls_line("drwxr-xr-x  2 user group  4096 2024-01-15 12:34 dirname")
    assert info == {"name": "dirname", "is_dir": True, "size": 4096, "mtime": pytest.approx(info["mtime"])}
    assert info["is_dir"] is True
    assert info["size"] == 4096
    assert info["name"] == "dirname"


def test_parse_ls_line_regular():
    from biome_fm.models.fish_vfs import _parse_ls_line
    info = _parse_ls_line("-rw-r--r--  1 user group  1234 2024-06-20 09:15 file.txt")
    assert info is not None
    assert info["is_dir"] is False
    assert info["size"] == 1234
    assert info["name"] == "file.txt"


def test_parse_ls_line_invalid():
    from biome_fm.models.fish_vfs import _parse_ls_line
    assert _parse_ls_line("total 8") is None
    assert _parse_ls_line("") is None


def test_listdir_skips_dot_entries():
    from biome_fm.models.fish_vfs import FISHVfs
    ls_output = (
        "drwxr-xr-x  2 root root 4096 2024-01-15 10:00 .\n"
        "drwxr-xr-x  5 root root 4096 2024-01-15 10:00 ..\n"
        "-rw-r--r--  1 user user  512 2024-01-15 11:00 readme.txt\n"
    )
    vfs = FISHVfs.__new__(FISHVfs)
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = ls_output.encode()
    vfs._client = MagicMock()
    vfs._client.exec_command.return_value = (None, mock_stdout, None)
    items = vfs.listdir(PurePosixPath("/home/user"))
    names = [i.name for i in items]
    assert "." not in names
    assert ".." not in names
    assert "readme.txt" in names


def test_listdir_parses_ls_output():
    from biome_fm.models.fish_vfs import FISHVfs
    from biome_fm.models.file_item import FileItem
    ls_output = (
        "drwxr-xr-x  2 user group 4096 2024-01-15 12:34 subdir\n"
        "-rw-r--r--  1 user group 1234 2024-06-20 09:15 file.txt\n"
    )
    vfs = FISHVfs.__new__(FISHVfs)
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = ls_output.encode()
    vfs._client = MagicMock()
    vfs._client.exec_command.return_value = (None, mock_stdout, None)
    items = vfs.listdir(PurePosixPath("/home/user"))
    assert len(items) == 2
    assert all(isinstance(i, FileItem) for i in items)
    dirs = [i for i in items if i.is_dir]
    files = [i for i in items if not i.is_dir]
    assert dirs[0].name == "subdir"
    assert files[0].name == "file.txt"
    assert files[0].size == 1234


def test_read_bytes_calls_cat():
    from biome_fm.models.fish_vfs import FISHVfs
    vfs = FISHVfs.__new__(FISHVfs)
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"hello world"
    vfs._client = MagicMock()
    vfs._client.exec_command.return_value = (None, mock_stdout, None)
    data = vfs.read_bytes(PurePosixPath("/etc/hosts"))
    assert data == b"hello world"
    cmd = vfs._client.exec_command.call_args[0][0]
    assert "cat" in cmd
    assert "/etc/hosts" in cmd
