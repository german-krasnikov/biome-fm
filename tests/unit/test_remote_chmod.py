"""Tests for remote chmod (F238)."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.commands.chmod_cmd import ChmodCmd
from biome_fm.models.file_item import FileItem


class FakeVFS:
    def __init__(self) -> None:
        self.chmod_calls: list[tuple] = []

    def chmod(self, path: Path, mode: int) -> None:
        self.chmod_calls.append((path, mode))


class TestSFTPChmod:
    def test_sftp_chmod_calls_sftp_client(self):
        paramiko = pytest.importorskip("paramiko")
        from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs

        session = SFTPSession(host="example.com")
        vfs = SFTPVfs(session)
        mock_sftp = MagicMock()
        vfs._sftp = mock_sftp

        vfs.chmod(PurePosixPath("/remote/file.txt"), 0o644)

        mock_sftp.chmod.assert_called_once_with("/remote/file.txt", 0o644)


class TestChmodCmdWithVFS:
    def test_chmod_cmd_delegates_to_vfs(self):
        vfs = FakeVFS()
        p = Path("/remote/file.txt")
        cmd = ChmodCmd([p], 0o755, vfs=vfs)
        cmd.execute()
        assert vfs.chmod_calls == [(p, 0o755)]

    def test_chmod_cmd_local_unchanged(self, tmp_path):
        """Without vfs param, falls back to os.chmod."""
        f = tmp_path / "test.txt"
        f.write_text("hi")
        cmd = ChmodCmd([f], 0o600)
        cmd.execute()
        mode = f.stat().st_mode & 0o777
        assert mode == 0o600
