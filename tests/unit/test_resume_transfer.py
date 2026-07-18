"""Unit tests for resume-on-partial-file in ProgressCopyCmd._copy_file()."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest

from biome_fm.commands.copy_cmd import ProgressCopyCmd


def _cmd(src: Path, dst: Path, chunk: int = 16) -> ProgressCopyCmd:
    return ProgressCopyCmd(
        sources=[src],
        dest_dir=dst.parent,
        vfs=None,
        cancel=threading.Event(),
        report=lambda *a: None,
        chunk=chunk,
    )


def _run_copy_file(cmd: ProgressCopyCmd, src: Path, dst: Path) -> None:
    cmd._copy_file(src, dst)


def test_no_resume_for_new_file(tmp_path: Path) -> None:
    """Dest doesn't exist → full copy, src content reproduced exactly."""
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    data = b"A" * 10 + b"B" * 90
    src.write_bytes(data)
    _run_copy_file(_cmd(src, dst), src, dst)
    assert dst.read_bytes() == data


def test_resume_skips_written_bytes(tmp_path: Path) -> None:
    """Partial dst (5 bytes of garbage) + src unchanged → append src[5:], preserving partial prefix."""
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    data = b"A" * 10 + b"B" * 90
    src.write_bytes(data)

    # Partial dst with different prefix bytes — proves we didn't overwrite
    partial = b"X" * 5
    dst.write_bytes(partial)

    # dst mtime must be newer than src mtime to signal "src unchanged"
    past = time.time() - 10
    os.utime(src, (past, past))  # src is older than dst

    _run_copy_file(_cmd(src, dst), src, dst)

    # seek-and-append: prefix preserved, rest from src[5:]
    assert dst.read_bytes() == partial + data[5:]


def test_resume_detects_source_mtime_change(tmp_path: Path) -> None:
    """src mtime newer than partial dst → source changed → full overwrite."""
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    data = b"A" * 10 + b"B" * 90
    src.write_bytes(data)

    partial = b"X" * 5
    dst.write_bytes(partial)

    # dst is older than src — source was modified after the partial write
    past = time.time() - 10
    os.utime(dst, (past, past))  # dst is old, src is fresh

    _run_copy_file(_cmd(src, dst), src, dst)

    assert dst.read_bytes() == data  # full overwrite, not append


def test_overwrite_action_skips_resume(tmp_path: Path) -> None:
    """When resolver returns OVERWRITE, dst must be fully overwritten — no resume."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    src = src_dir / "a.bin"
    data = b"A" * 100
    src.write_bytes(data)

    # Partial dst with favorable mtime (would trigger resume without guard)
    dst = dst_dir / "a.bin"
    dst.write_bytes(b"X" * 10)
    past = time.time() - 10
    os.utime(src, (past, past))

    from biome_fm.models.conflict_resolver import ConflictAction
    from biome_fm.models.vfs import LocalVFS

    cmd = ProgressCopyCmd(
        sources=[src],
        dest_dir=dst_dir,
        vfs=LocalVFS(),
        cancel=threading.Event(),
        report=lambda *a: None,
        strategy=ConflictAction.OVERWRITE_ALL,
    )
    cmd.execute()
    assert dst.read_bytes() == data  # full overwrite, not X*10 + A*90


def test_resume_partial_larger_than_source(tmp_path: Path) -> None:
    """dst size >= src size (corruption) → full overwrite."""
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"Z" * 50)

    # dst is larger than src
    dst.write_bytes(b"X" * 100)
    past = time.time() - 10
    os.utime(src, (past, past))

    _run_copy_file(_cmd(src, dst), src, dst)

    assert dst.read_bytes() == b"Z" * 50
