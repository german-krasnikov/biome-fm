"""Test reveal_in_finder utility."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.utils import platform as plat


class TestRevealInFinder:
    def test_mac_uses_open_R(self):
        with patch.object(plat, "IS_MAC", True), \
             patch.object(plat, "IS_WIN", False), \
             patch("subprocess.Popen") as mock:
            plat.reveal_in_finder(Path("/tmp/foo.txt"))
        mock.assert_called_once()
        cmd = mock.call_args[0][0]
        assert cmd == ["open", "-R", "/tmp/foo.txt"]

    def test_win_uses_explorer_select(self):
        with patch.object(plat, "IS_MAC", False), \
             patch.object(plat, "IS_WIN", True), \
             patch("subprocess.Popen") as mock:
            plat.reveal_in_finder(Path("/tmp/foo.txt"))
        mock.assert_called_once()
        cmd = mock.call_args[0][0]
        assert cmd == ["explorer", "/select,/tmp/foo.txt"]

    def test_linux_uses_xdg_open_parent(self):
        with patch.object(plat, "IS_MAC", False), \
             patch.object(plat, "IS_WIN", False), \
             patch("subprocess.Popen") as mock:
            plat.reveal_in_finder(Path("/tmp/sub/foo.txt"))
        mock.assert_called_once()
        cmd = mock.call_args[0][0]
        assert cmd == ["xdg-open", "/tmp/sub"]
