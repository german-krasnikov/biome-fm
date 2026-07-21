"""F421 — Remote File Search (Server-Side) unit tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# exec_find tests (test via real implementation after import)
# ---------------------------------------------------------------------------

def _make_sftp_vfs(stdout_lines: list[str]):
    """Return an SFTPVfs with a mocked _client."""
    from biome_fm.models.sftp_vfs import SFTPVfs, SFTPSession

    vfs = SFTPVfs.__new__(SFTPVfs)
    client = MagicMock()
    client.exec_command.return_value = (None, iter(stdout_lines), None)
    vfs._client = client
    return vfs


def test_exec_find_parses_stdout():
    vfs = _make_sftp_vfs(["/home/user/foo.py\n", "/home/user/bar.py\n"])
    result = vfs.exec_find("/home/user", "*.py")
    assert result == ["/home/user/foo.py", "/home/user/bar.py"]


def test_exec_find_uses_shlex_quote():
    vfs = _make_sftp_vfs([])
    vfs.exec_find("/home/my dir", "*.py")
    cmd_used = vfs._client.exec_command.call_args[0][0]
    assert "'/home/my dir'" in cmd_used


def test_exec_find_raises_when_not_connected():
    from biome_fm.models.sftp_vfs import SFTPVfs, SFTPSession

    vfs = SFTPVfs.__new__(SFTPVfs)
    vfs._client = None
    import pytest
    with pytest.raises(RuntimeError):
        vfs.exec_find("/home", "*.py")


# ---------------------------------------------------------------------------
# remote_search tests
# ---------------------------------------------------------------------------

def test_remote_search_no_exec_find():
    from biome_fm.presenters.search_presenter import remote_search

    result = remote_search(object(), "/home", "foo")
    assert result == []


def test_remote_search_wraps_pattern():
    from biome_fm.presenters.search_presenter import remote_search

    vfs = MagicMock()
    vfs.exec_find.return_value = []
    remote_search(vfs, "/home", "foo")
    vfs.exec_find.assert_called_once_with("/home", "*foo*")


def test_remote_search_returns_paths():
    from biome_fm.presenters.search_presenter import remote_search

    vfs = MagicMock()
    vfs.exec_find.return_value = ["/home/user/foo.py", "/home/user/bar.py"]
    result = remote_search(vfs, "/home/user", "foo")
    assert result == [Path("/home/user/foo.py"), Path("/home/user/bar.py")]


def test_remote_search_swallows_exceptions():
    from biome_fm.presenters.search_presenter import remote_search

    vfs = MagicMock()
    vfs.exec_find.side_effect = OSError("connection lost")
    assert remote_search(vfs, "/home", "foo") == []
