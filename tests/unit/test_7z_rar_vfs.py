"""Unit tests for SevenZipVFS and RarVFS — mocks only, no real archives."""
from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

ARCHIVE = Path("/fake/archive")


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_7z_entry(filename: str, size: int = 100, is_dir: bool = False) -> MagicMock:
    e = MagicMock()
    e.filename = filename
    e.uncompressed = size
    e.is_directory = is_dir
    e.creationtime = None
    return e


def _make_rar_entry(filename: str, file_size: int = 100, is_dir: bool = False) -> MagicMock:
    e = MagicMock()
    e.filename = filename
    e.file_size = file_size
    e.is_dir.return_value = is_dir
    e.mtime = MagicMock(timestamp=MagicMock(return_value=0.0))
    return e


# ── SevenZipVFS ──────────────────────────────────────────────────────────────

class TestSevenZipVFS:
    def _make_vfs(self, entries: list) -> "SevenZipVFS":  # noqa: F821
        mock_7z = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.list.return_value = entries
        mock_7z.SevenZipFile.return_value = ctx
        with patch.dict(sys.modules, {"py7zr": mock_7z}):
            from biome_fm.models.archive_7z import SevenZipVFS
            vfs = SevenZipVFS.__new__(SevenZipVFS)
            vfs._path = ARCHIVE / "test.7z"
            vfs._py7zr = mock_7z
        return vfs, mock_7z

    def test_7z_listdir_returns_items(self):
        entries = [_make_7z_entry("readme.txt", 42)]
        vfs, mock_7z = self._make_vfs(entries)

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.list.return_value = entries
        mock_7z.SevenZipFile.return_value = ctx

        items = vfs.listdir(vfs._path)
        assert len(items) == 1
        assert items[0].name == "readme.txt"
        assert items[0].size == 42
        assert not items[0].is_dir

    def test_7z_read_bytes(self):
        vfs, mock_7z = self._make_vfs([])

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = {"readme.txt": MagicMock(read=MagicMock(return_value=b"hello"))}
        mock_7z.SevenZipFile.return_value = ctx

        data = vfs.read_bytes(vfs._path / "readme.txt")
        assert data == b"hello"

    def test_7z_not_installed_raises(self):
        with patch.dict(sys.modules, {"py7zr": None}):
            # force reimport
            sys.modules.pop("biome_fm.models.archive_7z", None)
            from biome_fm.models.archive_7z import SevenZipVFS
            with pytest.raises(ImportError, match="py7zr"):
                SevenZipVFS(Path("/fake/test.7z"))
            sys.modules.pop("biome_fm.models.archive_7z", None)


# ── RarVFS ───────────────────────────────────────────────────────────────────

class TestRarVFS:
    def _make_vfs(self, entries: list) -> tuple:
        mock_rar = MagicMock()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.infolist.return_value = entries
        mock_rar.RarFile.return_value = ctx
        with patch.dict(sys.modules, {"rarfile": mock_rar}):
            sys.modules.pop("biome_fm.models.archive_7z", None)
            from biome_fm.models.archive_7z import RarVFS
            vfs = RarVFS.__new__(RarVFS)
            vfs._path = ARCHIVE / "test.rar"
            vfs._rarfile = mock_rar
        return vfs, mock_rar

    def test_rar_listdir_returns_items(self):
        entries = [_make_rar_entry("doc.pdf", 200)]
        vfs, mock_rar = self._make_vfs(entries)

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.infolist.return_value = entries
        mock_rar.RarFile.return_value = ctx

        items = vfs.listdir(vfs._path)
        assert len(items) == 1
        assert items[0].name == "doc.pdf"
        assert items[0].size == 200
        assert not items[0].is_dir

    def test_rar_read_bytes(self):
        vfs, mock_rar = self._make_vfs([])

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = b"world"
        mock_rar.RarFile.return_value = ctx

        data = vfs.read_bytes(vfs._path / "doc.pdf")
        assert data == b"world"

    def test_rar_not_installed_raises(self):
        with patch.dict(sys.modules, {"rarfile": None}):
            sys.modules.pop("biome_fm.models.archive_7z", None)
            from biome_fm.models.archive_7z import RarVFS
            with pytest.raises(ImportError, match="rarfile"):
                RarVFS(Path("/fake/test.rar"))
            sys.modules.pop("biome_fm.models.archive_7z", None)
