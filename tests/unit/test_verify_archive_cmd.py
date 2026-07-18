"""Tests for VerifyArchiveCmd (F206)."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from biome_fm.commands.archive_cmd import VerifyArchiveCmd


def _make_zip(path: Path) -> Path:
    """Create a valid zip at path, return path."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("hello.txt", "hello world")
    return path


def _make_tar(path: Path) -> Path:
    """Create a valid .tar.gz at path, return path."""
    with tarfile.open(path, "w:gz") as tf:
        import io
        data = b"hello"
        info = tarfile.TarInfo(name="hello.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    return path


def test_valid_zip_returns_empty(tmp_path: Path) -> None:
    archive = _make_zip(tmp_path / "test.zip")
    result = VerifyArchiveCmd(archive).execute()
    assert result == ""


def test_valid_tar_returns_empty(tmp_path: Path) -> None:
    archive = _make_tar(tmp_path / "test.tar.gz")
    result = VerifyArchiveCmd(archive).execute()
    assert result == ""


def test_corrupt_zip_returns_error(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    archive.write_bytes(b"PK\x03\x04" + b"\xff" * 50)  # fake PK header, garbage body
    result = VerifyArchiveCmd(archive).execute()
    assert result != ""


def test_unsupported_format_returns_error(tmp_path: Path) -> None:
    archive = tmp_path / "file.rar"
    archive.write_bytes(b"Rar!")
    result = VerifyArchiveCmd(archive).execute()
    assert "Unsupported" in result
