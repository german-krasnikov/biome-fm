"""F235 — Remote connection status event tests."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from biome_fm.event_bus import EventBus


class TestRemoteStatusEvents:
    def test_connect_publishes_event(self):
        from biome_fm.event_bus import RemoteConnected

        fake_bus = EventBus()
        received: list[RemoteConnected] = []
        fake_bus.subscribe(RemoteConnected, received.append)

        from biome_fm.models.vfs_router import VFSRouter
        router = VFSRouter(bus=fake_bus)
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", return_value=mock_vfs), \
             patch("biome_fm.models.sftp_vfs.SFTPSession"):
            router.listdir(Path("sftp://user@myhost:22/path"))

        assert len(received) == 1
        assert received[0].scheme == "sftp"
        assert received[0].host == "myhost"

    def test_connect_only_fires_once_per_connection(self):
        from biome_fm.event_bus import RemoteConnected

        fake_bus = EventBus()
        received: list[RemoteConnected] = []
        fake_bus.subscribe(RemoteConnected, received.append)

        from biome_fm.models.vfs_router import VFSRouter
        router = VFSRouter(bus=fake_bus)
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", return_value=mock_vfs), \
             patch("biome_fm.models.sftp_vfs.SFTPSession"):
            router.listdir(Path("sftp://user@myhost:22/path1"))
            router.listdir(Path("sftp://user@myhost:22/path2"))

        assert len(received) == 1  # only on first connect

    def test_disconnect_publishes_event(self):
        from biome_fm.event_bus import RemoteDisconnected

        fake_bus = EventBus()
        received: list[RemoteDisconnected] = []
        fake_bus.subscribe(RemoteDisconnected, received.append)

        from biome_fm.models.vfs_router import VFSRouter
        router = VFSRouter(bus=fake_bus)
        mock_vfs = MagicMock()
        mock_vfs.listdir.return_value = []

        with patch("biome_fm.models.sftp_vfs.SFTPVfs", return_value=mock_vfs), \
             patch("biome_fm.models.sftp_vfs.SFTPSession"):
            router.listdir(Path("sftp://user@myhost:22/path"))

        key = next(iter(router._remote))
        router.disconnect(key)

        assert len(received) == 1
        assert received[0].scheme == "sftp"
        assert received[0].host == "myhost"
