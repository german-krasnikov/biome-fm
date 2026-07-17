"""Unit tests for LocalVFS.copy() using os.sendfile with fallback."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.models.vfs import LocalVFS


@pytest.fixture
def vfs() -> LocalVFS:
    return LocalVFS()


def test_copy_file_content_preserved(tmp_path: Path, vfs: LocalVFS) -> None:
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_bytes(b"hello sendfile")

    vfs.copy(src, dst)

    assert dst.read_bytes() == b"hello sendfile"


def test_copy_falls_back_on_error(tmp_path: Path, vfs: LocalVFS) -> None:
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_bytes(b"fallback content")

    with patch("biome_fm.models.vfs.os.sendfile", side_effect=OSError("mock sendfile fail")):
        vfs.copy(src, dst)

    assert dst.read_bytes() == b"fallback content"
