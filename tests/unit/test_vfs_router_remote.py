"""F306 — VFS Router remote scheme dispatch tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.vfs_router import VFSRouter


class TestLocalPathUnaffected:
    def test_local_path_returns_local_vfs(self, tmp_path):
        router = VFSRouter()
        items = router.listdir(tmp_path)
        assert isinstance(items, list)

    def test_no_scheme_no_remote_dispatch(self, tmp_path):
        router = VFSRouter()
        # No _remote keys should be populated for local paths
        router.listdir(tmp_path)
        assert not router._remote


class TestSFTPDispatch:
    def test_sftp_scheme_detected_and_delegated(self):
        router = VFSRouter()
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        mock_sftp_cls = MagicMock(return_value=mock_vfs)
        mock_session_cls = MagicMock()

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", mock_sftp_cls), \
             patch("biome_fm.models.sftp_vfs.SFTPSession", mock_session_cls):
            router.listdir(Path("sftp://user@myhost:22/data"))

        mock_sftp_cls.assert_called_once()
        mock_vfs.connect.assert_called_once()
        mock_vfs.listdir.assert_called_once()

    def test_sftp_connection_cached(self):
        router = VFSRouter()
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", return_value=mock_vfs), \
             patch("biome_fm.models.sftp_vfs.SFTPSession"):
            router.listdir(Path("sftp://user@myhost:22/dir1"))
            router.listdir(Path("sftp://user@myhost:22/dir2"))

        # Should only connect once (connection reused)
        assert mock_vfs.connect.call_count == 1

    def test_ssh_scheme_also_uses_sftp(self):
        router = VFSRouter()
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", return_value=mock_vfs), \
             patch("biome_fm.models.sftp_vfs.SFTPSession"):
            router.listdir(Path("ssh://host/path"))

        mock_vfs.connect.assert_called_once()


class TestS3Dispatch:
    def test_s3_delegates_to_fsspec(self):
        router = VFSRouter()
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.fsspec_vfs.FsspecVFS", return_value=mock_vfs):
            router.listdir(Path("s3://my-bucket/prefix"))

        mock_vfs.listdir.assert_called_once()


class TestUnknownScheme:
    def test_unknown_scheme_raises_value_error(self):
        router = VFSRouter()
        with pytest.raises(ValueError, match="Unknown scheme"):
            router.listdir(Path("foobar://host/path"))


class TestResolvedPathDelegation:
    """C54 — router must pass resolved backend paths, not raw URI Paths."""

    def _make_fake_remote(self, calls: list) -> object:
        class FakeRemote:
            def listdir(self, p): return []
            def stat(self, p):
                from biome_fm.models.file_item import FileItem
                return FileItem(name="", path=p, is_dir=False, size=0, modified=0)
            def read_bytes(self, p): return b""
            def exists(self, p): return False
            def copy(self, src, dst): calls.append(("copy", src, dst))
            def move(self, src, dst): calls.append(("move", src, dst))
            def delete(self, p): ...
            def mkdir(self, p): ...
        return FakeRemote()

    def test_router_copy_delegates_resolved_path(self, tmp_path):
        calls: list = []
        router = VFSRouter()
        router._remote["sftp://u@h:"] = self._make_fake_remote(calls)
        router.copy(Path("sftp://u@h/a.txt"), tmp_path / "b.txt")
        assert calls[0][1] == Path("/a.txt")  # resolved path, not raw URI

    def test_router_move_delegates_resolved_path(self):
        calls: list = []
        router = VFSRouter()
        router._remote["sftp://u@h:"] = self._make_fake_remote(calls)
        router.move(Path("sftp://u@h/a.txt"), Path("sftp://u@h/b.txt"))
        assert calls[0][1:] == (Path("/a.txt"), Path("/b.txt"))  # resolved paths


class TestDisconnect:
    def test_disconnect_removes_from_cache(self):
        router = VFSRouter()
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", return_value=mock_vfs), \
             patch("biome_fm.models.sftp_vfs.SFTPSession"):
            router.listdir(Path("sftp://user@host:22/path"))

        assert router._remote  # something is cached
        key = next(iter(router._remote))
        router.disconnect(key)
        assert not router._remote
        mock_vfs.disconnect.assert_called_once()
