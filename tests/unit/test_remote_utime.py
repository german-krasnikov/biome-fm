"""Unit tests for utime() on SFTPVfs and FsspecVFS."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs
from biome_fm.models.fsspec_vfs import FsspecVFS


# --- SFTPVfs ---

def test_sftp_vfs_utime_calls_paramiko():
    vfs = SFTPVfs(SFTPSession(host="h"))
    captured = {}

    def fake_reconnect(fn, *args):
        captured["fn"] = fn
        captured["args"] = args
        mock_sftp = MagicMock()
        fn(mock_sftp, *args)
        captured["sftp"] = mock_sftp

    with patch.object(vfs, "_with_reconnect", side_effect=fake_reconnect):
        vfs.utime(PurePosixPath("/remote/file"), 1234567890.0)

    captured["sftp"].utime.assert_called_once_with("/remote/file", (1234567890.0, 1234567890.0))


# --- FsspecVFS ---

def _make_fsspec_vfs(mock_fs) -> FsspecVFS:
    vfs = object.__new__(FsspecVFS)
    vfs._fs = mock_fs
    return vfs


def test_fsspec_vfs_utime_with_support():
    mock_fs = MagicMock(spec=["utime"])
    vfs = _make_fsspec_vfs(mock_fs)
    vfs.utime(Path("/bucket/file.txt"), 1234567890.0)
    mock_fs.utime.assert_called_once_with("/bucket/file.txt", (1234567890.0, 1234567890.0))


def test_fsspec_vfs_utime_no_support():
    mock_fs = MagicMock(spec=[])  # no utime attribute
    vfs = _make_fsspec_vfs(mock_fs)
    vfs.utime(Path("/bucket/file.txt"), 1234567890.0)  # must not raise
