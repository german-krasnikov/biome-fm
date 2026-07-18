"""Unit tests for cross-VFS extraction (archive → local copy)."""
from __future__ import annotations

import io
import threading
import zipfile
import tarfile
from pathlib import Path

import pytest

from biome_fm.models.archive_vfs import ArchiveVFS
from biome_fm.models.vfs_router import VFSRouter
from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.operations.task import Cancelled


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_zip(path: Path, files: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return path


def _make_tar(path: Path, files: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in files.items():
            buf = io.BytesIO(data)
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, buf)
    return path


def _noop(*_): pass


# ── ArchiveVFS.open_file ──────────────────────────────────────────────────────

def test_archive_vfs_open_file_zip(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {"hello.txt": b"world"})
    vfs = ArchiveVFS(arc)
    with vfs.open_file(arc / "hello.txt") as f:
        assert f.read() == b"world"


def test_archive_vfs_open_file_tar(tmp_path: Path) -> None:
    arc = _make_tar(tmp_path / "a.tar.gz", {"hello.txt": b"contents"})
    vfs = ArchiveVFS(arc)
    with vfs.open_file(arc / "hello.txt") as f:
        assert f.read() == b"contents"


def test_archive_vfs_open_file_nested_zip(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {"sub/deep.txt": b"deep"})
    vfs = ArchiveVFS(arc)
    with vfs.open_file(arc / "sub" / "deep.txt") as f:
        assert f.read() == b"deep"


# ── VFSRouter.copy (archive → local) ─────────────────────────────────────────

def test_vfs_router_copy_single_file_from_zip(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {"file.txt": b"extracted"})
    dst = tmp_path / "out" / "file.txt"
    router = VFSRouter()
    router.copy(arc / "file.txt", dst)
    assert dst.read_bytes() == b"extracted"


def test_vfs_router_copy_dir_from_zip_preserves_structure(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {
        "mydir/a.txt": b"aaa",
        "mydir/sub/b.txt": b"bbb",
    })
    dst = tmp_path / "out" / "mydir"
    router = VFSRouter()
    router.copy(arc / "mydir", dst)
    assert (dst / "a.txt").read_bytes() == b"aaa"
    assert (dst / "sub" / "b.txt").read_bytes() == b"bbb"


def test_vfs_router_copy_single_file_from_tar(tmp_path: Path) -> None:
    arc = _make_tar(tmp_path / "a.tar.gz", {"file.txt": b"tar-content"})
    dst = tmp_path / "out" / "file.txt"
    router = VFSRouter()
    router.copy(arc / "file.txt", dst)
    assert dst.read_bytes() == b"tar-content"


# ── ProgressCopyCmd with archive sources ─────────────────────────────────────

def test_progress_copy_cmd_extracts_from_archive(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {"file.txt": b"hello"})
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    cancel = threading.Event()
    router = VFSRouter()

    cmd = ProgressCopyCmd(
        sources=[arc / "file.txt"],
        dest_dir=dst_dir,
        vfs=router,
        cancel=cancel,
        report=_noop,
    )
    cmd.execute()
    assert (dst_dir / "file.txt").read_bytes() == b"hello"


def test_progress_copy_cmd_extracts_multiple_files(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {
        "a.txt": b"AAA",
        "b.txt": b"BBB",
    })
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    cancel = threading.Event()
    router = VFSRouter()

    cmd = ProgressCopyCmd(
        sources=[arc / "a.txt", arc / "b.txt"],
        dest_dir=dst_dir,
        vfs=router,
        cancel=cancel,
        report=_noop,
    )
    cmd.execute()
    assert (dst_dir / "a.txt").read_bytes() == b"AAA"
    assert (dst_dir / "b.txt").read_bytes() == b"BBB"


def test_progress_copy_cmd_reports_progress_during_archive_extract(tmp_path: Path) -> None:
    data = b"x" * (1024 * 4)
    arc = _make_zip(tmp_path / "a.zip", {"file.txt": data})
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    cancel = threading.Event()
    router = VFSRouter()

    reports: list[tuple] = []
    cmd = ProgressCopyCmd(
        sources=[arc / "file.txt"],
        dest_dir=dst_dir,
        vfs=router,
        cancel=cancel,
        report=lambda *a: reports.append(a),
        chunk=1024,
    )
    cmd.execute()
    assert (dst_dir / "file.txt").read_bytes() == data
    assert len(reports) > 1  # multiple progress calls


def test_progress_copy_cmd_extracts_archive_dir(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {
        "mydir/a.txt": b"aaa",
        "mydir/sub/b.txt": b"bbb",
    })
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    cancel = threading.Event()
    router = VFSRouter()
    cmd = ProgressCopyCmd(
        sources=[arc / "mydir"],
        dest_dir=dst_dir,
        vfs=router,
        cancel=cancel,
        report=_noop,
    )
    cmd.execute()
    assert (dst_dir / "mydir" / "a.txt").read_bytes() == b"aaa"
    assert (dst_dir / "mydir" / "sub" / "b.txt").read_bytes() == b"bbb"


def test_progress_copy_cmd_cancel_during_archive_dir_extract(tmp_path: Path) -> None:
    arc = _make_zip(tmp_path / "a.zip", {
        "mydir/a.txt": b"x" * 1024,
        "mydir/b.txt": b"y" * 1024,
        "mydir/c.txt": b"z" * 1024,
    })
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    cancel = threading.Event()
    router = VFSRouter()
    call_count = 0

    def cancel_after_first_file(*_):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            cancel.set()

    cmd = ProgressCopyCmd(
        sources=[arc / "mydir"],
        dest_dir=dst_dir,
        vfs=router,
        cancel=cancel,
        report=cancel_after_first_file,
    )
    with pytest.raises(Cancelled):
        cmd.execute()
    assert not (dst_dir / "mydir").exists()


def test_progress_copy_cmd_cancel_during_archive_extract(tmp_path: Path) -> None:
    data = b"x" * (512 * 1024)  # 512 KB, needs multiple 256 KB chunks
    arc = _make_zip(tmp_path / "a.zip", {"big.txt": data})
    dst_dir = tmp_path / "out"
    dst_dir.mkdir()
    cancel = threading.Event()
    router = VFSRouter()

    def cancel_on_first_report(*_):
        cancel.set()

    cmd = ProgressCopyCmd(
        sources=[arc / "big.txt"],
        dest_dir=dst_dir,
        vfs=router,
        cancel=cancel,
        report=cancel_on_first_report,
    )
    with pytest.raises(Cancelled):
        cmd.execute()
    assert not (dst_dir / "big.txt").exists()
