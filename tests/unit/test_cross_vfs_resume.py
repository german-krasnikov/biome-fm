"""TDD tests for F401 — Transfer Resume for Remote VFS (SFTP/S3)."""
from __future__ import annotations

import io
import threading
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs


def _cmd(src_vfs, tmp_path, src: Path | None = None):
    src = src or tmp_path / "src.bin"
    return ProgressCopyCmd(
        sources=[src],
        dest_dir=tmp_path / "dst",
        vfs=None,
        cancel=threading.Event(),
        report=lambda *a: None,
        src_vfs=src_vfs,
    )


# ---------------------------------------------------------------------------
# test 1 — streaming via open_read
# ---------------------------------------------------------------------------
def test_cross_vfs_streaming(tmp_path):
    data = b"hello world"
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst" / "src.bin"

    @contextmanager
    def _open_read(path, offset=0):
        yield io.BytesIO(data)

    src_vfs = MagicMock(spec=["open_read"])
    src_vfs.open_read = _open_read

    _cmd(src_vfs, tmp_path, src)._copy_cross_vfs(src, dst)
    assert dst.read_bytes() == data


# ---------------------------------------------------------------------------
# test 2 — resume appends from correct offset
# ---------------------------------------------------------------------------
def test_cross_vfs_resume_appends(tmp_path):
    full = b"0123456789"
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst" / "src.bin"
    dst.parent.mkdir()
    dst.write_bytes(full[:5])  # partial download

    seen_offset: list[int] = []

    @contextmanager
    def _open_read(path, offset=0):
        seen_offset.append(offset)
        yield io.BytesIO(full[offset:])

    fi = MagicMock()
    fi.size = 10
    fi.modified = None

    src_vfs = MagicMock(spec=["open_read", "stat"])
    src_vfs.open_read = _open_read
    src_vfs.stat.return_value = fi

    _cmd(src_vfs, tmp_path, src)._copy_cross_vfs(src, dst)

    assert seen_offset == [5]
    assert dst.read_bytes() == full


# ---------------------------------------------------------------------------
# test 3 — fallback to read_bytes when open_read absent
# ---------------------------------------------------------------------------
def test_cross_vfs_fallback_no_open_read(tmp_path):
    data = b"fallback bytes"
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst" / "src.bin"

    src_vfs = MagicMock(spec=["read_bytes"])
    src_vfs.read_bytes.return_value = data

    _cmd(src_vfs, tmp_path, src)._copy_cross_vfs(src, dst)

    src_vfs.read_bytes.assert_called_once_with(src)
    assert dst.read_bytes() == data


# ---------------------------------------------------------------------------
# test 4 — SFTPVfs.open_read calls seek(offset) on the file handle
# ---------------------------------------------------------------------------
def test_sftp_open_read_seeks():
    vfs = SFTPVfs(SFTPSession(host="localhost"))
    fh = MagicMock()

    with patch.object(vfs, "_with_reconnect", return_value=fh):
        with vfs.open_read(PurePosixPath("/remote/file.bin"), offset=100) as f:
            assert f is fh

    fh.seek.assert_called_once_with(100)
    fh.close.assert_called_once()
