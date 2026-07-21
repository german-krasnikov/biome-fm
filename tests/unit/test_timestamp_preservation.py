"""TDD: F437 — Remote File Timestamp Preservation."""
from __future__ import annotations

import threading
from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.file_item import FileItem


# ---------------------------------------------------------------------------
# _copy_cross_vfs tests
# ---------------------------------------------------------------------------

def _make_cmd(src_vfs, dest_dir: Path):
    """Minimal ProgressCopyCmd setup for cross-VFS copy tests."""
    from biome_fm.commands.copy_cmd import ProgressCopyCmd

    cancel = threading.Event()
    report = lambda *a: None
    cmd = ProgressCopyCmd(
        sources=[],
        dest_dir=dest_dir,
        vfs=None,
        cancel=cancel,
        report=report,
        src_vfs=src_vfs,
    )
    return cmd


def test_cross_vfs_preserves_mtime(tmp_path):
    """After cross-VFS copy, dst mtime matches remote stat().modified."""
    remote_mtime = 1_000_000.0
    src = Path("/remote/file.txt")
    dst = tmp_path / "file.txt"

    src_vfs = MagicMock(spec=["read_bytes", "stat"])
    src_vfs.read_bytes.return_value = b"hello"
    src_vfs.stat.return_value = FileItem(
        name="file.txt",
        path=src,
        is_dir=False,
        size=5,
        modified=remote_mtime,
    )

    cmd = _make_cmd(src_vfs, tmp_path)
    cmd._copy_cross_vfs(src, dst)

    assert dst.stat().st_mtime == pytest.approx(remote_mtime)


def test_cross_vfs_no_stat_still_works(tmp_path):
    """Cross-VFS copy succeeds when src_vfs has no stat() (backward compat)."""
    src = Path("/remote/file.txt")
    dst = tmp_path / "file.txt"

    src_vfs = MagicMock(spec=["read_bytes"])  # no stat attribute
    src_vfs.read_bytes.return_value = b"data"

    cmd = _make_cmd(src_vfs, tmp_path)
    cmd._copy_cross_vfs(src, dst)  # must not raise

    assert dst.read_bytes() == b"data"


# ---------------------------------------------------------------------------
# SFTPVfs.stat tests
# ---------------------------------------------------------------------------

def test_sftp_stat_returns_file_item():
    """SFTPVfs.stat() returns FileItem with correct name, size, modified."""
    from biome_fm.models.sftp_vfs import SFTPVfs, SFTPSession

    vfs = SFTPVfs(SFTPSession(host="localhost"))

    fake_attrs = MagicMock()
    fake_attrs.st_mode = 0o100644  # regular file
    fake_attrs.st_size = 1234
    fake_attrs.st_mtime = 1_000_000.0

    # Patch _with_reconnect to call fn(fake_sftp, path) directly
    fake_sftp = MagicMock()
    fake_sftp.stat.return_value = fake_attrs

    path = PurePosixPath("/remote/file.txt")

    with patch.object(vfs, "_with_reconnect", side_effect=lambda fn, *args: fn(fake_sftp, *args)):
        item = vfs.stat(path)

    assert item.name == "file.txt"
    assert item.size == 1234
    assert item.modified == 1_000_000.0
    assert item.is_dir is False


def test_sftp_stat_detects_directory():
    """SFTPVfs.stat() sets is_dir=True for directory mode."""
    import stat as stat_mod
    from biome_fm.models.sftp_vfs import SFTPVfs, SFTPSession

    vfs = SFTPVfs(SFTPSession(host="localhost"))

    fake_attrs = MagicMock()
    fake_attrs.st_mode = stat_mod.S_IFDIR | 0o755
    fake_attrs.st_size = 0
    fake_attrs.st_mtime = 0.0

    fake_sftp = MagicMock()
    fake_sftp.stat.return_value = fake_attrs

    path = PurePosixPath("/remote/mydir")

    with patch.object(vfs, "_with_reconnect", side_effect=lambda fn, *args: fn(fake_sftp, *args)):
        item = vfs.stat(path)

    assert item.is_dir is True
