"""Tests for ArchiveCmd and ExtractCmd."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from biome_fm.commands.archive_cmd import ArchiveCmd, ExtractCmd


# ── ArchiveCmd ──────────────────────────────────────────────────────────────

def test_archive_cmd_creates_zip(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_text("hello")
    archive = tmp_path / "out.zip"
    ArchiveCmd([src], archive).execute()
    assert archive.exists()
    assert zipfile.is_zipfile(archive)


def test_archive_cmd_zip_contains_files(tmp_path: Path) -> None:
    src = tmp_path / "hello.txt"
    src.write_text("world")
    archive = tmp_path / "out.zip"
    ArchiveCmd([src], archive).execute()
    with zipfile.ZipFile(archive) as zf:
        assert "hello.txt" in zf.namelist()


def test_archive_cmd_undo_deletes_archive(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_text("x")
    archive = tmp_path / "out.zip"
    cmd = ArchiveCmd([src], archive)
    cmd.execute()
    assert archive.exists()
    cmd.undo()
    assert not archive.exists()


def test_archive_cmd_undo_missing_ok(tmp_path: Path) -> None:
    """undo() on a never-executed cmd should not raise."""
    archive = tmp_path / "ghost.zip"
    ArchiveCmd([], archive).undo()  # no error


def test_archive_cmd_directory_recursive(tmp_path: Path) -> None:
    d = tmp_path / "mydir"
    d.mkdir()
    (d / "sub").mkdir()
    (d / "sub" / "deep.txt").write_text("deep")
    (d / "top.txt").write_text("top")
    archive = tmp_path / "out.zip"
    ArchiveCmd([d], archive).execute()
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
    assert any("deep.txt" in n for n in names)
    assert any("top.txt" in n for n in names)


def test_archive_cmd_description(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    cmd = ArchiveCmd([src, src], tmp_path / "out.zip")
    assert "2" in cmd.description


def test_archive_cmd_is_undoable() -> None:
    assert ArchiveCmd([], Path("/tmp/x.zip")).undoable is True


# ── ExtractCmd ──────────────────────────────────────────────────────────────

def test_extract_cmd_zip(tmp_path: Path) -> None:
    archive = tmp_path / "test.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("file.txt", "content")
    dest = tmp_path / "out"
    dest.mkdir()
    ExtractCmd(archive, dest).execute()
    assert (dest / "file.txt").exists()


def test_extract_cmd_tar_gz(tmp_path: Path) -> None:
    archive = tmp_path / "test.tar.gz"
    src = tmp_path / "file.txt"
    src.write_text("hello")
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(src, arcname="file.txt")
    dest = tmp_path / "out"
    dest.mkdir()
    ExtractCmd(archive, dest).execute()
    assert (dest / "file.txt").exists()


def test_extract_cmd_not_undoable() -> None:
    assert ExtractCmd(Path("/tmp/x.zip"), Path("/tmp/out")).undoable is False
