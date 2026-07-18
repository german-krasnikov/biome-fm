"""F233 — SFTP connection pool / channel reuse tests."""
from __future__ import annotations

import sys
import threading
import types
from unittest.mock import MagicMock, patch

import pytest


def _make_sftp_vfs(max_channels: int = 4):
    """Build SFTPVfs with a mock paramiko injected so we can test pool logic."""
    # Build a fake paramiko module
    fake_paramiko = types.ModuleType("paramiko")
    fake_sftp_client = MagicMock(name="SFTPClient")
    fake_paramiko.SSHClient = MagicMock(return_value=MagicMock())
    fake_paramiko.WarningPolicy = MagicMock()
    fake_paramiko.SFTPClient = fake_sftp_client

    with patch.dict(sys.modules, {"paramiko": fake_paramiko}):
        # Force reimport of sftp_vfs with our fake paramiko
        import importlib
        import biome_fm.models.sftp_vfs as _mod
        _orig = (_mod._HAS_PARAMIKO, _mod._paramiko)
        _mod._HAS_PARAMIKO = True
        _mod._paramiko = fake_paramiko

        from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs

        session = SFTPSession(host="test", port=22, user="u")
        vfs = SFTPVfs(session, max_channels=max_channels)

        # Manually set a fake sftp connection (bypass real connect)
        fake_ssh = MagicMock(name="SSHClient_instance")
        fake_sftp = MagicMock(name="sftp_instance")
        fake_ssh.open_sftp.return_value = fake_sftp
        fake_ssh.get_transport.return_value = None
        vfs._client = fake_ssh
        vfs._sftp = fake_sftp
        # Reset pool state
        vfs._channels = []

        return vfs, _orig, _mod


@pytest.fixture
def sftp_vfs_pool():
    vfs, _orig, _mod = _make_sftp_vfs(max_channels=4)
    yield vfs
    # Restore
    _mod._HAS_PARAMIKO, _mod._paramiko = _orig


class TestChannelReuse:
    def test_get_and_return_channel(self, sftp_vfs_pool):
        vfs = sftp_vfs_pool
        ch = vfs._get_channel()
        assert ch is not None
        vfs._return_channel(ch)
        # Pool should now have one channel ready
        assert len(vfs._channels) == 1

    def test_channel_reused_from_pool(self, sftp_vfs_pool):
        vfs = sftp_vfs_pool
        ch1 = vfs._get_channel()
        vfs._return_channel(ch1)
        ch2 = vfs._get_channel()
        # Same object reused
        assert ch1 is ch2

    def test_new_channel_opened_when_pool_empty(self, sftp_vfs_pool):
        vfs = sftp_vfs_pool
        # Pool is empty initially
        assert vfs._channels == []
        ch = vfs._get_channel()
        # A new channel was created (open_sftp called)
        assert ch is not None


class TestMaxChannels:
    def test_max_channels_blocks_then_unblocks(self):
        vfs, _orig, _mod = _make_sftp_vfs(max_channels=2)
        try:
            # Grab all channels
            ch1 = vfs._get_channel()
            ch2 = vfs._get_channel()

            result = []
            unblocked = threading.Event()

            def _grab_third():
                ch = vfs._get_channel()
                result.append(ch)
                unblocked.set()

            t = threading.Thread(target=_grab_third, daemon=True)
            t.start()

            # Should be blocked — wait 100ms, result should still be empty
            assert not unblocked.wait(0.1), "should have blocked"

            # Release one channel → third grab should unblock
            vfs._return_channel(ch1)
            assert unblocked.wait(1.0), "should have unblocked after return"
            assert len(result) == 1
        finally:
            _mod._HAS_PARAMIKO, _mod._paramiko = _orig
