"""Regression guard: CopyCmd partial failure leaves completed files on disk."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.copy_cmd import CopyCmd


class _PartialFailVFS:
    """Raises OSError on the 2nd copy call; performs the 1st copy for real."""

    def __init__(self) -> None:
        self._count = 0

    def copy(self, src: Path, dst: Path) -> None:
        self._count += 1
        if self._count == 1:
            dst.write_bytes(src.read_bytes())
        else:
            raise OSError("disk full")

    def delete(self, path: Path) -> None:
        path.unlink(missing_ok=True)


def test_partial_copy_failure_leaves_completed_files(tmp_path: Path) -> None:
    """A bare cmd.execute() never rolled back; rollback lived in CommandHistory.
    After undo() removal partial copies stay on disk — that is the accepted behaviour.
    """
    src = tmp_path / "src"
    src.mkdir()
    first = src / "first.txt"
    second = src / "second.txt"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    dst = tmp_path / "dst"
    dst.mkdir()

    cmd = CopyCmd([first, second], dst, _PartialFailVFS())
    with pytest.raises(OSError):
        cmd.execute()

    # The first file was copied before the failure — it stays on disk.
    assert (dst / "first.txt").exists()
