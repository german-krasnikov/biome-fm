"""Tests for RemoteEditCmd (F258)."""
from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch


class FakeVFS:
    def __init__(self, data: bytes = b"hello") -> None:
        self._data = data
        self.written: bytes | None = None

    def read_bytes(self, path: Path) -> bytes:
        return self._data

    def write_bytes(self, path: Path, data: bytes) -> None:
        self.written = data


class TestRemoteEditCmd:
    def test_execute_downloads_opens_uploads(self, tmp_path):
        from biome_fm.commands.remote_edit_cmd import RemoteEditCmd

        vfs = FakeVFS(b"original content")
        cmd = RemoteEditCmd(Path("/remote/file.txt"), vfs, "nano")

        def fake_run(args, check):
            # Simulate editor modifying the file
            with open(args[-1], "wb") as f:
                f.write(b"modified content")
            # Touch mtime
            t = time.time() + 1
            os.utime(args[-1], (t, t))

        with patch("biome_fm.commands.remote_edit_cmd.subprocess.run", side_effect=fake_run):
            cmd.execute()

        assert vfs.written == b"modified content"

    def test_no_upload_if_mtime_unchanged(self, tmp_path):
        from biome_fm.commands.remote_edit_cmd import RemoteEditCmd

        vfs = FakeVFS(b"unchanged")
        cmd = RemoteEditCmd(Path("/remote/file.txt"), vfs, "nano")

        def fake_run(args, check):
            pass  # editor does nothing — mtime stays same

        with patch("biome_fm.commands.remote_edit_cmd.subprocess.run", side_effect=fake_run):
            cmd.execute()

        assert vfs.written is None

    def test_tempfile_cleaned_up(self, tmp_path):
        from biome_fm.commands.remote_edit_cmd import RemoteEditCmd

        vfs = FakeVFS(b"data")
        tmp_paths: list[str] = []
        cmd = RemoteEditCmd(Path("/remote/file.txt"), vfs, "nano")

        original_mkstemp = __import__("tempfile").mkstemp

        def capturing_mkstemp(**kwargs):
            fd, path = original_mkstemp(**kwargs)
            tmp_paths.append(path)
            return fd, path

        with patch("biome_fm.commands.remote_edit_cmd.tempfile.mkstemp", side_effect=capturing_mkstemp):
            with patch("biome_fm.commands.remote_edit_cmd.subprocess.run"):
                cmd.execute()

        assert tmp_paths, "mkstemp was never called"
        for p in tmp_paths:
            assert not os.path.exists(p), f"Temp file not cleaned up: {p}"

    def test_undoable_is_false(self):
        from biome_fm.commands.remote_edit_cmd import RemoteEditCmd

        assert RemoteEditCmd.undoable is False
