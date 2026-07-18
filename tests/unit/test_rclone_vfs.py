"""TDD: RcloneVFS — rclone subprocess backend (F240)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


_LSJSON_RESPONSE = json.dumps([
    {
        "Path": "docs",
        "Name": "docs",
        "Size": -1,
        "MimeType": "inode/directory",
        "ModTime": "2024-01-15T10:30:00Z",
        "IsDir": True,
    },
    {
        "Path": "readme.txt",
        "Name": "readme.txt",
        "Size": 512,
        "MimeType": "text/plain",
        "ModTime": "2024-01-14T08:00:00.000000000Z",
        "IsDir": False,
    },
])


def test_available_false_when_no_binary() -> None:
    with patch("shutil.which", return_value=None):
        from biome_fm.models import rclone_vfs
        assert rclone_vfs.RcloneVFS.available() is False


def test_not_available_raises_on_construct() -> None:
    with patch("shutil.which", return_value=None):
        from biome_fm.models.rclone_vfs import RcloneVFS
        with pytest.raises(RuntimeError, match="rclone not found"):
            RcloneVFS("gdrive:")


def test_listdir_parses_json() -> None:
    with patch("shutil.which", return_value="/usr/bin/rclone"), \
         patch("subprocess.check_output", return_value=_LSJSON_RESPONSE) as mock_out:
        from biome_fm.models.rclone_vfs import RcloneVFS
        vfs = RcloneVFS("gdrive:")
        items = vfs.listdir(Path("/"))

    assert len(items) == 2
    dirs = [i for i in items if i.is_dir]
    files = [i for i in items if not i.is_dir]
    assert dirs[0].name == "docs"
    assert files[0].name == "readme.txt"
    assert files[0].size == 512
    mock_out.assert_called_once_with(
        ["rclone", "lsjson", "gdrive:/"], text=True
    )


def test_copy_calls_rclone_copyto() -> None:
    with patch("shutil.which", return_value="/usr/bin/rclone"), \
         patch("subprocess.check_call") as mock_call:
        from biome_fm.models.rclone_vfs import RcloneVFS
        vfs = RcloneVFS("gdrive:")
        vfs.copy(Path("/local/file.txt"), Path("/remote/file.txt"))

    mock_call.assert_called_once_with(
        ["rclone", "copyto", "/local/file.txt", "gdrive:/remote/file.txt"]
    )


def test_delete_calls_rclone_deletefile() -> None:
    with patch("shutil.which", return_value="/usr/bin/rclone"), \
         patch("subprocess.check_call") as mock_call:
        from biome_fm.models.rclone_vfs import RcloneVFS
        vfs = RcloneVFS("gdrive:")
        vfs.delete(Path("/docs/old.txt"))

    mock_call.assert_called_once_with(
        ["rclone", "deletefile", "gdrive:/docs/old.txt"]
    )


def test_mkdir_calls_rclone_mkdir() -> None:
    with patch("shutil.which", return_value="/usr/bin/rclone"), \
         patch("subprocess.check_call") as mock_call:
        from biome_fm.models.rclone_vfs import RcloneVFS
        vfs = RcloneVFS("gdrive:")
        vfs.mkdir(Path("/newdir"))

    mock_call.assert_called_once_with(
        ["rclone", "mkdir", "gdrive:/newdir"]
    )


def test_rclone_path_combines_remote_and_path() -> None:
    with patch("shutil.which", return_value="/usr/bin/rclone"):
        from biome_fm.models.rclone_vfs import RcloneVFS
        vfs = RcloneVFS("s3:mybucket")
        assert vfs._rclone_path(Path("/prefix/file.txt")) == "s3:mybucket/prefix/file.txt"
