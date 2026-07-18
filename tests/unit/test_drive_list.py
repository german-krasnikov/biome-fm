"""Tests for drive/volume listing logic."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.presenters.drive_list import VolumeInfo, list_volumes


def _make_vol(root: str, name: str, free: int, total: int, valid=True, ready=True):
    v = MagicMock()
    v.rootPath.return_value = root
    v.displayName.return_value = name
    v.bytesFree.return_value = free
    v.bytesTotal.return_value = total
    v.isValid.return_value = valid
    v.isReady.return_value = ready
    return v


@patch("biome_fm.presenters.drive_list.QStorageInfo")
def test_list_volumes_returns_paths(mock_qsi):
    mock_qsi.mountedVolumes.return_value = [
        _make_vol("/", "Macintosh HD", 100, 500),
        _make_vol("/Volumes/USB", "USB", 50, 200),
    ]
    result = list_volumes()
    assert [v.root for v in result] == [Path("/"), Path("/Volumes/USB")]


@patch("biome_fm.presenters.drive_list.QStorageInfo")
def test_volume_info_includes_free_space(mock_qsi):
    mock_qsi.mountedVolumes.return_value = [
        _make_vol("/", "HD", 1024, 4096),
    ]
    result = list_volumes()
    assert result[0].free_bytes == 1024
    assert result[0].total_bytes == 4096
    assert result[0].name == "HD"


@patch("biome_fm.presenters.drive_list.QStorageInfo")
def test_empty_volumes(mock_qsi):
    mock_qsi.mountedVolumes.return_value = []
    assert list_volumes() == []


@patch("biome_fm.presenters.drive_list.QStorageInfo")
def test_skips_invalid_or_not_ready(mock_qsi):
    mock_qsi.mountedVolumes.return_value = [
        _make_vol("/", "HD", 100, 500),
        _make_vol("/bad", "Bad", 0, 0, valid=False),
        _make_vol("/slow", "Slow", 0, 0, ready=False),
    ]
    result = list_volumes()
    assert len(result) == 1
    assert result[0].root == Path("/")
