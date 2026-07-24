"""Unit tests for DockerVFS — uses ls_parser for parse logic."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.models.docker_vfs import DockerVFS, _docker_available


_PARENT = Path("/")


def _run_listdir(lines: str, parent: Path = _PARENT) -> list:
    """Helper: simulate DockerVFS.listdir with mocked _exec output."""
    with patch("biome_fm.models.docker_vfs._docker_available", return_value=True):
        vfs = DockerVFS("testcontainer")
    with patch.object(vfs, "_exec", return_value=lines):
        return vfs.listdir(parent)


def test_parse_file():
    line = "-rw-r--r--  1 root root  1234 2024-06-20 09:15 file.txt"
    items = _run_listdir(line + "\n")
    assert len(items) == 1
    fi = items[0]
    assert fi.name == "file.txt"
    assert fi.path == Path("/file.txt")
    assert fi.is_dir is False
    assert fi.size == 1234


def test_parse_dir():
    line = "drwxr-xr-x  2 root root  4096 2024-01-15 12:34 subdir"
    items = _run_listdir(line + "\n")
    assert len(items) == 1
    assert items[0].is_dir is True
    assert items[0].name == "subdir"


def test_parse_symlink_strips_target():
    line = "lrwxrwxrwx  1 root root     7 2024-01-01 00:00 link -> target"
    items = _run_listdir(line + "\n")
    assert len(items) == 1
    assert items[0].name == "link"


def test_skips_dotdot():
    lines = (
        "drwxr-xr-x  2 root root  4096 2024-01-15 12:34 .\n"
        "drwxr-xr-x  2 root root  4096 2024-01-15 12:34 ..\n"
        "-rw-r--r--  1 root root    42 2024-01-15 12:34 keep.txt\n"
    )
    items = _run_listdir(lines)
    assert len(items) == 1
    assert items[0].name == "keep.txt"


def test_docker_available_false():
    with patch("biome_fm.models.docker_vfs.shutil.which", return_value=None):
        assert _docker_available() is False


def test_docker_vfs_requires_docker():
    with patch("biome_fm.models.docker_vfs._docker_available", return_value=False):
        with pytest.raises(RuntimeError, match="docker CLI"):
            DockerVFS("test")
