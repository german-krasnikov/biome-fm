"""Unit tests for SFTP keep-alive and auto-reconnect (F041)."""
from __future__ import annotations

from pathlib import PurePosixPath
from unittest.mock import MagicMock, call, patch

import pytest


class _FakeSSHException(Exception):
    """Stand-in for paramiko.SSHException."""


def _make_fake_paramiko() -> MagicMock:
    m = MagicMock()
    m.SSHException = _FakeSSHException
    m.WarningPolicy = MagicMock
    return m


@pytest.fixture()
def fake_paramiko() -> MagicMock:
    return _make_fake_paramiko()


@pytest.fixture()
def vfs(fake_paramiko):
    from biome_fm.models import sftp_vfs as _mod
    from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs

    session = SFTPSession(host="h", port=22, user="u", remote_path="/")
    ssh_errors = (_FakeSSHException, ConnectionError, EOFError)

    with (
        patch.object(_mod, "_HAS_PARAMIKO", True),
        patch.object(_mod, "_paramiko", fake_paramiko),
        patch.object(_mod, "_SSH_ERRORS", ssh_errors),
    ):
        yield SFTPVfs(session)


def _wire_connected(vfs, fake_paramiko) -> MagicMock:
    """Connect vfs and return the mock sftp object."""
    mock_sftp = MagicMock()
    fake_paramiko.SSHClient.return_value.open_sftp.return_value = mock_sftp
    vfs.connect()
    return mock_sftp


class TestKeepalive:
    def test_keepalive_set_on_connect(self, vfs, fake_paramiko):
        mock_transport = MagicMock()
        fake_paramiko.SSHClient.return_value.get_transport.return_value = mock_transport

        vfs.connect()

        mock_transport.set_keepalive.assert_called_once_with(30)


class TestReconnect:
    def test_reconnect_on_ssh_exception(self, vfs, fake_paramiko):
        mock_sftp = _wire_connected(vfs, fake_paramiko)
        mock_sftp.listdir_attr.side_effect = [_FakeSSHException("drop"), []]

        with patch("biome_fm.models.sftp_vfs.time.sleep"):
            result = vfs.listdir(PurePosixPath("/"))

        assert result == []
        # SSHClient constructed twice: initial connect + one reconnect
        assert fake_paramiko.SSHClient.call_count == 2

    def test_reconnect_max_3_attempts(self, vfs, fake_paramiko):
        mock_sftp = _wire_connected(vfs, fake_paramiko)
        mock_sftp.listdir_attr.side_effect = _FakeSSHException("always fails")

        with (
            patch("biome_fm.models.sftp_vfs.time.sleep") as mock_sleep,
            pytest.raises(_FakeSSHException),
        ):
            vfs.listdir(PurePosixPath("/"))

        # 4 total calls: attempt 0 (initial), then 3 reconnect attempts
        assert mock_sftp.listdir_attr.call_count == 4
        # backoff: 1s, 2s, 4s
        assert mock_sleep.call_args_list == [call(1), call(2), call(4)]

    def test_connect_failure_during_reconnect(self, vfs, fake_paramiko):
        """connect() raising during retry should itself be retried, not abort."""
        mock_sftp = _wire_connected(vfs, fake_paramiko)
        mock_sftp.listdir_attr.side_effect = _FakeSSHException("drop")
        # All subsequent reconnect calls fail too
        fake_paramiko.SSHClient.return_value.connect.side_effect = _FakeSSHException("no route")

        with (
            patch("biome_fm.models.sftp_vfs.time.sleep") as mock_sleep,
            pytest.raises(_FakeSSHException),
        ):
            vfs.listdir(PurePosixPath("/"))

        # 1 initial + 3 reconnect SSHClient() calls = 4 total
        assert fake_paramiko.SSHClient.call_count == 4
        assert mock_sleep.call_args_list == [call(1), call(2), call(4)]

    def test_reconnect_preserves_path_arg(self, vfs, fake_paramiko):
        mock_sftp = _wire_connected(vfs, fake_paramiko)
        mock_sftp.listdir_attr.side_effect = [_FakeSSHException("drop"), []]

        with patch("biome_fm.models.sftp_vfs.time.sleep"):
            vfs.listdir(PurePosixPath("/home/user"))

        # After reconnect, listdir_attr called with the same original path
        assert mock_sftp.listdir_attr.call_args == call("/home/user")

    def test_write_bytes_reconnect(self, vfs, fake_paramiko):
        mock_sftp = _wire_connected(vfs, fake_paramiko)
        mock_file = MagicMock()
        mock_sftp.open.side_effect = [_FakeSSHException("drop"), mock_file]
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch("biome_fm.models.sftp_vfs.time.sleep"):
            vfs.write_bytes(PurePosixPath("/tmp/f.txt"), b"data")

        assert fake_paramiko.SSHClient.call_count == 2
        mock_file.write.assert_called_once_with(b"data")

    def test_no_reconnect_on_non_ssh_error(self, vfs, fake_paramiko):
        mock_sftp = _wire_connected(vfs, fake_paramiko)
        mock_sftp.listdir_attr.side_effect = ValueError("not an ssh error")

        with pytest.raises(ValueError):
            vfs.listdir(PurePosixPath("/"))

        assert mock_sftp.listdir_attr.call_count == 1
        assert fake_paramiko.SSHClient.call_count == 1  # no reconnect attempt
