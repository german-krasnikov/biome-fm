"""Integration: MkdirCmd.undo() refuses to delete non-empty directories (C09)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.mkdir_cmd import MkdirCmd
from biome_fm.models.vfs import LocalVFS


def test_mkdir_undo_raises_on_nonempty_dir(tmp_path: Path) -> None:
    # C09: undo() must raise OSError instead of rmtree-ing a non-empty dir
    d = tmp_path / "newdir"
    d.mkdir()
    (d / "file.txt").write_text("keep me")

    vfs = LocalVFS()
    cmd = MkdirCmd(d, vfs)

    with pytest.raises(OSError):
        cmd.undo()

    # dir and file must still exist
    assert d.exists()
    assert (d / "file.txt").exists()
