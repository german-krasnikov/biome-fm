"""Tests for share_files() — F410 macOS Share Sheet."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.utils.platform import share_files


def test_share_files_noop_non_mac(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("biome_fm.utils.platform.IS_MAC", False)
    monkeypatch.setattr("biome_fm.utils.platform.subprocess.Popen", mock)
    share_files([Path("/tmp/x")])
    mock.assert_not_called()


def test_share_files_calls_open_on_mac(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("biome_fm.utils.platform.IS_MAC", True)
    monkeypatch.setattr("biome_fm.utils.platform.subprocess.Popen", mock)
    share_files([Path("/a"), Path("/b")])
    mock.assert_called_once()
    args = mock.call_args[0][0]
    assert args == ["open", "--share", "/a", "/b"]


def test_share_files_empty_list(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("biome_fm.utils.platform.IS_MAC", True)
    monkeypatch.setattr("biome_fm.utils.platform.subprocess.Popen", mock)
    share_files([])
    mock.assert_not_called()
