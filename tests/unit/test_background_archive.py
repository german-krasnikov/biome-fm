"""Tests for ProgressArchiveCmd — background archive creation with cancel + progress."""
from __future__ import annotations

import tarfile
import threading
import zipfile
from pathlib import Path

import pytest

from biome_fm.commands.archive_cmd import ProgressArchiveCmd
from biome_fm.operations.task import Cancelled


@pytest.fixture()
def src_files(tmp_path: Path) -> list[Path]:
    files = []
    for i in range(3):
        f = tmp_path / f"file{i}.txt"
        f.write_text(f"content {i}")
        files.append(f)
    return files


def test_progress_archive_creates_zip(src_files: list[Path], tmp_path: Path) -> None:
    dest = tmp_path / "out.zip"
    cancel = threading.Event()
    ProgressArchiveCmd(src_files, dest, "zip", cancel, lambda *_: None).execute()
    assert dest.exists()
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert set(names) == {"file0.txt", "file1.txt", "file2.txt"}


def test_progress_reported_per_file(src_files: list[Path], tmp_path: Path) -> None:
    dest = tmp_path / "out.zip"
    cancel = threading.Event()
    calls: list = []
    ProgressArchiveCmd(src_files, dest, "zip", cancel, lambda *a: calls.append(a)).execute()
    assert len(calls) == len(src_files)
    for i, call in enumerate(calls):
        file_idx, total, b_done, b_total, name = call
        assert file_idx == i + 1
        assert total == len(src_files)
        assert b_done == 0
        assert b_total == 0
        assert name in {f.name for f in src_files}


def test_cancel_deletes_partial_archive(src_files: list[Path], tmp_path: Path) -> None:
    dest = tmp_path / "out.zip"
    cancel = threading.Event()
    call_count = 0

    def report(*_: object) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            cancel.set()

    with pytest.raises(Cancelled):
        ProgressArchiveCmd(src_files, dest, "zip", cancel, report).execute()

    assert not dest.exists()


def test_progress_archive_undo_deletes_dest(src_files: list[Path], tmp_path: Path) -> None:
    dest = tmp_path / "out.zip"
    cancel = threading.Event()
    cmd = ProgressArchiveCmd(src_files, dest, "zip", cancel, lambda *_: None)
    cmd.execute()
    assert dest.exists()
    cmd.undo()
    assert not dest.exists()


def test_invalid_format_raises(src_files: list[Path], tmp_path: Path) -> None:
    dest = tmp_path / "out.7z"
    cancel = threading.Event()
    with pytest.raises(ValueError, match="Unknown archive format"):
        ProgressArchiveCmd(src_files, dest, "7z", cancel, lambda *_: None).execute()


def test_zip_directory_source(tmp_path: Path) -> None:
    d = tmp_path / "mydir"
    d.mkdir()
    (d / "a.txt").write_text("aaa")
    sub = d / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("bbb")
    dest = tmp_path / "out.zip"
    cancel = threading.Event()
    ProgressArchiveCmd([d], dest, "zip", cancel, lambda *_: None).execute()
    with zipfile.ZipFile(dest) as zf:
        names = set(zf.namelist())
    assert "mydir/a.txt" in names
    assert "mydir/sub/b.txt" in names


def test_cancel_during_directory_rglob(tmp_path: Path) -> None:
    d = tmp_path / "big"
    d.mkdir()
    for i in range(20):
        (d / f"f{i}.txt").write_text(f"data{i}")
    dest = tmp_path / "out.zip"
    cancel = threading.Event()
    cancel.set()  # pre-cancel
    with pytest.raises(Cancelled):
        ProgressArchiveCmd([d], dest, "zip", cancel, lambda *_: None).execute()
    assert not dest.exists()


def test_tar_gz_format(src_files: list[Path], tmp_path: Path) -> None:
    dest = tmp_path / "out.tar.gz"
    cancel = threading.Event()
    calls: list = []
    ProgressArchiveCmd(src_files, dest, "tar.gz", cancel, lambda *a: calls.append(a)).execute()
    assert dest.exists()
    with tarfile.open(dest, "r:gz") as tf:
        names = tf.getnames()
    assert set(names) == {"file0.txt", "file1.txt", "file2.txt"}
    assert len(calls) == len(src_files)
