"""Unit tests for S3 object versioning — F434."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import biome_fm.models.fsspec_vfs as _mod


# ---------------------------------------------------------------------------
# FsspecVFS.list_versions
# ---------------------------------------------------------------------------

def _make_vfs(fs_attrs: list[str] | None = None):
    """Return (vfs, mock_fs) with fs spec limited to fs_attrs if given."""
    spec = fs_attrs if fs_attrs is not None else ["ls", "info", "object_version_info"]
    mock_fs = MagicMock(spec=spec)
    with patch.object(_mod, "fsspec") as mock_fsspec:
        mock_fsspec.filesystem.return_value = mock_fs
        from biome_fm.models.fsspec_vfs import FsspecVFS
        vfs = FsspecVFS("s3://bucket")
    return vfs, mock_fs


def test_list_versions_returns_empty_on_non_s3():
    vfs, _ = _make_vfs(fs_attrs=["ls", "info"])  # no object_version_info
    assert vfs.list_versions(Path("bucket/file.txt")) == []


def test_list_versions_returns_versions():
    vfs, mock_fs = _make_vfs()
    versions = [{"VersionId": "v1", "IsLatest": True, "Size": 42, "LastModified": "2024-01-01"}]
    mock_fs.object_version_info.return_value = versions
    assert vfs.list_versions(Path("bucket/file.txt")) == versions
    mock_fs.object_version_info.assert_called_once_with("bucket/file.txt")


def test_list_versions_exception_returns_empty():
    vfs, mock_fs = _make_vfs()
    mock_fs.object_version_info.side_effect = Exception("access denied")
    assert vfs.list_versions(Path("bucket/file.txt")) == []


# ---------------------------------------------------------------------------
# S3VersionsDialog
# ---------------------------------------------------------------------------

FAKE_VERSIONS = [
    {"VersionId": "abc123", "LastModified": "2024-01-01", "Size": 100, "IsLatest": True},
    {"VersionId": "def456", "LastModified": "2023-12-01", "Size": 90, "IsLatest": False},
    {"VersionId": "ghi789", "LastModified": "2023-11-01", "Size": 80, "IsLatest": False},
]


def test_s3_versions_dialog_row_count(qtbot):
    from biome_fm.views.s3_versions_dialog import S3VersionsDialog

    dlg = S3VersionsDialog(Path("bucket/file.txt"), FAKE_VERSIONS)
    qtbot.addWidget(dlg)
    assert dlg._table.rowCount() == 3


def test_s3_versions_dialog_restore_emits_signal(qtbot):
    from biome_fm.views.s3_versions_dialog import S3VersionsDialog

    dlg = S3VersionsDialog(Path("bucket/file.txt"), FAKE_VERSIONS)
    qtbot.addWidget(dlg)
    dlg._table.setCurrentCell(0, 0)

    with qtbot.waitSignal(dlg.restore_requested, timeout=1000) as blocker:
        dlg._on_restore()

    assert blocker.args == ["abc123"]
