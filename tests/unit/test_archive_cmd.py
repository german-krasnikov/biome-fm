"""Tests for ArchiveCmd and ExtractCmd."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path
from unittest.mock import patch

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


@patch("biome_fm.commands.archive_cmd.zipfile.ZipFile")
def test_archive_execute_self_cleans_on_failure(mock_zip_cls, tmp_path: Path) -> None:
    """REGRESSION GUARD: execute() unlinks archive file on failure (self-cleaning inline)."""
    mock_zip_cls.return_value.__enter__.return_value.write.side_effect = OSError("disk full")
    archive = tmp_path / "out.zip"
    archive.touch()  # simulate partial file created before error
    src = tmp_path / "a.txt"
    src.write_text("ok")
    cmd = ArchiveCmd([src], archive)
    with pytest.raises((RuntimeError, OSError)):
        cmd.execute()
    assert not archive.exists()


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


# ── Security: Zip Slip prevention ────────────────────────────────────────────

def test_extract_zip_slip_raises(tmp_path: Path) -> None:
    bad_zip = tmp_path / "evil.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../evil.txt", "pwned")
    dest = tmp_path / "dest"
    dest.mkdir()
    cmd = ExtractCmd(bad_zip, dest)
    with pytest.raises((ValueError, RuntimeError)):
        cmd.execute()
    assert not (tmp_path / "evil.txt").exists()


def test_extract_absolute_path_raises(tmp_path: Path) -> None:
    bad_zip = tmp_path / "abs.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("/etc/passwd", "root:x:0:0")
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises((ValueError, RuntimeError)):
        ExtractCmd(bad_zip, dest).execute()


def test_extract_safe_zip_succeeds(tmp_path: Path) -> None:
    good_zip = tmp_path / "good.zip"
    with zipfile.ZipFile(good_zip, "w") as zf:
        zf.writestr("readme.txt", "hello")
        zf.writestr("subdir/file.txt", "world")
    dest = tmp_path / "dest"
    dest.mkdir()
    ExtractCmd(good_zip, dest).execute()
    assert (dest / "readme.txt").read_text() == "hello"
    assert (dest / "subdir" / "file.txt").read_text() == "world"
