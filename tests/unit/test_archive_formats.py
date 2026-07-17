"""Tests for multi-format ArchiveCmd (tar.gz, tar.bz2, zip)."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from biome_fm.commands.archive_cmd import ArchiveCmd


def _make_src(tmp_path: Path) -> Path:
    src = tmp_path / "hello.txt"
    src.write_text("world")
    return src


def test_zip_still_works(tmp_path: Path) -> None:
    src = _make_src(tmp_path)
    archive = tmp_path / "out.zip"
    ArchiveCmd([src], archive, fmt="zip").execute()
    assert zipfile.is_zipfile(archive)


def test_tar_gz_created(tmp_path: Path) -> None:
    src = _make_src(tmp_path)
    archive = tmp_path / "out.tar.gz"
    ArchiveCmd([src], archive, fmt="tar.gz").execute()
    assert tarfile.is_tarfile(archive)
    with tarfile.open(archive, "r:gz") as tf:
        assert "hello.txt" in tf.getnames()


def test_tar_bz2_created(tmp_path: Path) -> None:
    src = _make_src(tmp_path)
    archive = tmp_path / "out.tar.bz2"
    ArchiveCmd([src], archive, fmt="tar.bz2").execute()
    assert tarfile.is_tarfile(archive)
    with tarfile.open(archive, "r:bz2") as tf:
        assert "hello.txt" in tf.getnames()


def test_tar_gz_undo_deletes(tmp_path: Path) -> None:
    src = _make_src(tmp_path)
    archive = tmp_path / "out.tar.gz"
    cmd = ArchiveCmd([src], archive, fmt="tar.gz")
    cmd.execute()
    cmd.undo()
    assert not archive.exists()
