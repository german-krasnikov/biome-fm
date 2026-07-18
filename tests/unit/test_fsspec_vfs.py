"""Unit tests for FsspecVFS — all fsspec calls are mocked."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import biome_fm.models.fsspec_vfs as _mod


@pytest.fixture()
def mock_fs():
    return MagicMock()


@pytest.fixture()
def vfs(mock_fs):
    """FsspecVFS with fsspec module-level name patched to a mock."""
    with patch.object(_mod, "fsspec") as mock_fsspec:
        mock_fsspec.filesystem.return_value = mock_fs
        from biome_fm.models.fsspec_vfs import FsspecVFS
        yield FsspecVFS("s3://my-bucket"), mock_fs


def test_listdir_returns_file_items(vfs):
    fsvfs, fs = vfs
    now = time.time()
    fs.ls.return_value = [
        {"name": "bucket/folder/", "type": "directory", "size": 0, "mtime": now},
        {"name": "bucket/file.txt", "type": "file", "size": 1234, "mtime": now},
    ]
    items = fsvfs.listdir(Path("bucket"))
    assert len(items) == 2
    assert items[0].is_dir is True
    assert items[0].name == "folder"
    assert items[1].name == "file.txt"
    assert items[1].size == 1234
    assert items[1].is_dir is False


def test_stat_returns_file_item(vfs):
    fsvfs, fs = vfs
    now = time.time()
    fs.info.return_value = {
        "name": "bucket/file.txt",
        "type": "file",
        "size": 42,
        "mtime": now,
    }
    item = fsvfs.stat(Path("bucket/file.txt"))
    assert item.name == "file.txt"
    assert item.size == 42
    assert item.is_dir is False
    assert item.modified == now


def test_stat_handles_LastModified_datetime(vfs):
    """S3-style LastModified datetime object should convert to float timestamp."""
    from datetime import datetime, timezone
    fsvfs, fs = vfs
    dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    fs.info.return_value = {
        "name": "bucket/obj.bin",
        "type": "file",
        "size": 99,
        "LastModified": dt,
    }
    item = fsvfs.stat(Path("bucket/obj.bin"))
    assert item.modified == dt.timestamp()


def test_exists_delegates_to_fs(vfs):
    fsvfs, fs = vfs
    fs.exists.return_value = True
    assert fsvfs.exists(Path("bucket/file.txt")) is True
    fs.exists.assert_called_once_with("bucket/file.txt")


def test_read_bytes_delegates_to_fs(vfs):
    fsvfs, fs = vfs
    fs.cat_file.return_value = b"hello world"
    result = fsvfs.read_bytes(Path("bucket/file.txt"))
    assert result == b"hello world"
    fs.cat_file.assert_called_once_with("bucket/file.txt")


def test_copy_local_to_remote(vfs, tmp_path):
    """Local src → remote dst uses fs.put."""
    fsvfs, fs = vfs
    src = tmp_path / "local.txt"
    src.write_text("data")
    fsvfs.copy(src, Path("bucket/remote.txt"))
    fs.put.assert_called_once_with(str(src), "bucket/remote.txt")


def test_copy_remote_to_local(vfs, tmp_path):
    """Non-existent local src → treated as remote; uses fs.get."""
    fsvfs, fs = vfs
    dst = tmp_path / "out.txt"
    fsvfs.copy(Path("bucket/remote.txt"), dst)
    fs.get.assert_called_once_with("bucket/remote.txt", str(dst))


def test_unsupported_protocol_raises():
    """Unknown protocol forwarded to fsspec which raises ValueError."""
    with patch.object(_mod, "fsspec") as mock_fsspec:
        mock_fsspec.filesystem.side_effect = ValueError("unknown protocol: xyz")
        from biome_fm.models.fsspec_vfs import FsspecVFS
        with pytest.raises(ValueError, match="unknown protocol"):
            FsspecVFS("xyz://something")
