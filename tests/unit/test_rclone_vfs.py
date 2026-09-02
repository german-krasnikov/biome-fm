"""TDD: RcloneVFS — rclone subprocess backend (F240)."""
from __future__ import annotations

import json
import subprocess as _sp
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


_STAT_RESPONSE = json.dumps(
    {"Name": "f.txt", "IsDir": False, "Size": 42, "ModTime": "2024-01-01T00:00:00Z"}
)


def _make_rclone_vfs(remote: str = "gdrive:"):
    with patch("shutil.which", return_value="/usr/bin/rclone"):
        from biome_fm.models.rclone_vfs import RcloneVFS
        return RcloneVFS(remote)


def test_rclone_exists_true() -> None:
    vfs = _make_rclone_vfs()
    with patch("subprocess.check_output", return_value=_STAT_RESPONSE):
        assert vfs.exists(Path("/f.txt")) is True


def test_rclone_exists_false() -> None:
    vfs = _make_rclone_vfs()
    with patch("subprocess.check_output", side_effect=_sp.CalledProcessError(3, "rclone")):
        assert vfs.exists(Path("/missing.txt")) is False


def test_rclone_stat_returns_file_item() -> None:
    vfs = _make_rclone_vfs()
    with patch("subprocess.check_output", return_value=_STAT_RESPONSE):
        item = vfs.stat(Path("/f.txt"))
    assert item.name == "f.txt"
    assert item.size == 42


def test_rclone_move_calls_moveto() -> None:
    vfs = _make_rclone_vfs()
    src = Path("/src/file.txt")
    dst = Path("/dst/file.txt")
    # exists(dst) -> stat raises CalledProcessError -> False
    with patch("subprocess.check_output", side_effect=_sp.CalledProcessError(3, "rclone")), \
         patch("subprocess.check_call") as mock_call:
        vfs.move(src, dst)
    mock_call.assert_called_once_with(
        ["rclone", "moveto", vfs._rclone_path(src), vfs._rclone_path(dst)]
    )


def test_rclone_move_raises_file_exists() -> None:
    vfs = _make_rclone_vfs()
    dst = Path("/dst/file.txt")
    with (
        patch("subprocess.check_output", return_value=_STAT_RESPONSE),
        patch("subprocess.check_call") as mock_call,
        pytest.raises(FileExistsError),
    ):
        vfs.move(Path("/src/file.txt"), dst)
    mock_call.assert_not_called()


def test_rclone_stat_empty_list_raises_called_process_error() -> None:
    """Old rclone returning [] for missing path must not IndexError."""
    vfs = _make_rclone_vfs()
    with patch("subprocess.check_output", return_value="[]"), pytest.raises(_sp.CalledProcessError):
        vfs.stat(Path("/missing.txt"))
