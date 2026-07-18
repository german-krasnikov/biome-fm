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
