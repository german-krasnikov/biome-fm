"""Unit tests for DockerVFS — pure parse logic + mock-based init."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.models.docker_vfs import DockerVFS, _docker_available, _parse_docker_ls


_PARENT = Path("/")


def test_parse_docker_ls_file():
    line = "-rw-r--r--  1 root root  1234 2024-06-20 09:15 file.txt"
    items = _parse_docker_ls(line + "\n", _PARENT)
    assert len(items) == 1
    fi = items[0]
    assert fi.name == "file.txt"
    assert fi.path == Path("/file.txt")
    assert fi.is_dir is False
    assert fi.size == 1234


def test_parse_docker_ls_dir():
    line = "drwxr-xr-x  2 root root  4096 2024-01-15 12:34 subdir"
    items = _parse_docker_ls(line + "\n", _PARENT)
    assert len(items) == 1
    assert items[0].is_dir is True
    assert items[0].name == "subdir"


def test_parse_docker_ls_symlink():
    line = "lrwxrwxrwx  1 root root     7 2024-01-01 00:00 link -> target"
    items = _parse_docker_ls(line + "\n", _PARENT)
    assert len(items) == 1
    assert items[0].name == "link"


def test_parse_docker_ls_skips_dotdot():
    lines = (
        "drwxr-xr-x  2 root root  4096 2024-01-15 12:34 .\n"
        "drwxr-xr-x  2 root root  4096 2024-01-15 12:34 ..\n"
        "-rw-r--r--  1 root root    42 2024-01-15 12:34 keep.txt\n"
    )
    items = _parse_docker_ls(lines, _PARENT)
    assert len(items) == 1
    assert items[0].name == "keep.txt"


def test_docker_available_false():
    with patch("biome_fm.models.docker_vfs.shutil.which", return_value=None):
        assert _docker_available() is False


def test_docker_vfs_requires_docker():
    with patch("biome_fm.models.docker_vfs._docker_available", return_value=False):
        with pytest.raises(RuntimeError, match="docker CLI"):
            DockerVFS("test")
