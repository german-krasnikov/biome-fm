"""Tests for SymlinkCmd and HardlinkCmd."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _src(tmp_path: Path, name: str = "target.txt") -> Path:
    p = tmp_path / name
    p.write_text("content")
    return p


class TestSymlinkCmd:
    def test_creates_symlink(self, tmp_path: Path) -> None:
        from biome_fm.commands.symlink_cmd import SymlinkCmd

        target = _src(tmp_path)
        link = tmp_path / "link.txt"
        SymlinkCmd(target, link).execute()
        assert link.is_symlink()
        assert link.resolve() == target.resolve()

    def test_undo_removes(self, tmp_path: Path) -> None:
        from biome_fm.commands.symlink_cmd import SymlinkCmd

        target = _src(tmp_path)
        link = tmp_path / "link.txt"
        cmd = SymlinkCmd(target, link)
        cmd.execute()
        cmd.undo()
        assert not link.exists()
        assert not link.is_symlink()

    def test_is_undoable(self) -> None:
        from biome_fm.commands.symlink_cmd import SymlinkCmd
        assert SymlinkCmd(Path("/a"), Path("/b")).undoable is True


class TestHardlinkCmd:
    def test_hardlink_creates(self, tmp_path: Path) -> None:
        from biome_fm.commands.symlink_cmd import HardlinkCmd

        target = _src(tmp_path)
        link = tmp_path / "hard.txt"
        HardlinkCmd(target, link).execute()
        assert link.exists()
        assert link.stat().st_ino == target.stat().st_ino

    def test_hardlink_undo(self, tmp_path: Path) -> None:
        from biome_fm.commands.symlink_cmd import HardlinkCmd

        target = _src(tmp_path)
        link = tmp_path / "hard.txt"
        cmd = HardlinkCmd(target, link)
        cmd.execute()
        cmd.undo()
        assert not link.exists()


class TestFileItemSymlink:
    def test_is_symlink_field(self) -> None:
        item = FileItem(
            name="link", path=Path("/tmp/link"),
            is_dir=False, size=0, modified=0.0, is_symlink=True,
        )
        assert item.is_symlink is True

    def test_default_is_false(self) -> None:
        item = FileItem(name="f", path=Path("/tmp/f"), is_dir=False, size=0, modified=0.0)
        assert item.is_symlink is False


class TestLocalVFSSymlink:
    def test_listdir_sets_is_symlink(self, tmp_path: Path) -> None:
        from biome_fm.models.vfs import LocalVFS

        target = tmp_path / "real.txt"
        target.write_text("x")
        link = tmp_path / "soft.txt"
        link.symlink_to(target)

        items = {i.name: i for i in LocalVFS().listdir(tmp_path)}
        assert items["soft.txt"].is_symlink is True
        assert items["real.txt"].is_symlink is False
