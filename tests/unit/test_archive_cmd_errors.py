"""Error-handling tests for ArchiveCmd / ExtractCmd."""
from __future__ import annotations

import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.commands.archive_cmd import ArchiveCmd, ExtractCmd


def test_bad_zip_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip file")
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises((RuntimeError, zipfile.BadZipFile, OSError)):
        ExtractCmd(bad, dest).execute()


def test_permission_error_handled(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_text("x")
    archive = tmp_path / "out.zip"
    with patch("zipfile.ZipFile", side_effect=PermissionError("denied")):
        with pytest.raises((PermissionError, RuntimeError, OSError)):
            ArchiveCmd([src], archive).execute()


def test_extract_bad_tar_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.tar.gz"
    bad.write_bytes(b"garbage")
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises((RuntimeError, OSError, Exception)):
        ExtractCmd(bad, dest).execute()
