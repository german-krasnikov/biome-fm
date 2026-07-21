"""Unit tests for cross-VFS copy operations (F236)."""
from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock


def test_copy_local_to_local_unchanged(tmp_path: Path) -> None:
    """Default behavior (no src_vfs) copies via local filesystem."""
    from biome_fm.commands.copy_cmd import ProgressCopyCmd
    from biome_fm.models.vfs import LocalVFS

    src = tmp_path / "src"
    src.mkdir()
    f = src / "a.txt"
    f.write_bytes(b"hello")
    dst = tmp_path / "dst"
    dst.mkdir()

    cancel = threading.Event()
    report = MagicMock()
    vfs = LocalVFS()
    cmd = ProgressCopyCmd([f], dst, vfs, cancel, report)
    cmd.execute()

    assert (dst / "a.txt").read_bytes() == b"hello"
    assert cmd._src_vfs is None


def test_copy_with_src_vfs_reads_from_vfs(tmp_path: Path) -> None:
    """When src_vfs is provided, read_bytes is called on it."""
    from biome_fm.commands.copy_cmd import ProgressCopyCmd
    from biome_fm.models.vfs import LocalVFS

    dst = tmp_path / "dst"
    dst.mkdir()

    mock_vfs = MagicMock(spec=["read_bytes"])
    mock_vfs.read_bytes.return_value = b"vfs-data"

    fake_src = Path("/archive/file.txt")  # non-existent locally

    cancel = threading.Event()
    report = MagicMock()
    local_vfs = LocalVFS()

    cmd = ProgressCopyCmd([fake_src], dst, local_vfs, cancel, report, src_vfs=mock_vfs)
    cmd.execute()

    mock_vfs.read_bytes.assert_called_once_with(fake_src)
    assert (dst / "file.txt").read_bytes() == b"vfs-data"


def test_source_vfs_property() -> None:
    """ManagerPresenter._source_vfs returns active pane's vfs."""
    from unittest.mock import MagicMock

    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.manager_presenter import ManagerPresenter

    left = MagicMock()
    right = MagicMock()
    left_vfs = MagicMock()
    right_vfs = MagicMock()
    left.vfs = left_vfs
    right.vfs = right_vfs

    manager = ManagerPresenter(left, right, LocalVFS())
    manager.set_active_pane("left")

    assert manager._source_vfs is left_vfs


def test_target_vfs_property() -> None:
    """ManagerPresenter._target_vfs returns inactive pane's vfs."""
    from unittest.mock import MagicMock

    from biome_fm.models.vfs import LocalVFS
    from biome_fm.presenters.manager_presenter import ManagerPresenter

    left = MagicMock()
    right = MagicMock()
    left_vfs = MagicMock()
    right_vfs = MagicMock()
    left.vfs = left_vfs
    right.vfs = right_vfs

    manager = ManagerPresenter(left, right, LocalVFS())
    manager.set_active_pane("left")

    assert manager._target_vfs is right_vfs
