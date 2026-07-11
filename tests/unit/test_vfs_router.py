"""Tests for VFSRouter — transparent dispatch by path type."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from biome_fm.models.archive_vfs import ArchiveVFS
from biome_fm.models.vfs_router import VFSRouter


@pytest.fixture
def zip_archive(tmp_path: Path) -> Path:
    archive = tmp_path / "test.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("inside.txt", "content")
        zf.writestr("sub/child.txt", "nested")
    return archive


def test_plain_dir_uses_local(tmp_path: Path) -> None:
    (tmp_path / "afile.txt").write_text("hi")
    router = VFSRouter()
    items = router.listdir(tmp_path)
    assert any(i.name == "afile.txt" for i in items)


def test_zip_path_uses_archive(zip_archive: Path) -> None:
    router = VFSRouter()
    items = router.listdir(zip_archive)
    assert any(i.name == "inside.txt" for i in items)


def test_nested_path_same_cache(zip_archive: Path) -> None:
    router = VFSRouter()
    router.listdir(zip_archive)
    router.listdir(zip_archive / "sub")
    assert len(router._cache) == 1
    assert isinstance(router._cache[zip_archive], ArchiveVFS)


def test_parent_of_archive_uses_local(zip_archive: Path) -> None:
    router = VFSRouter()
    items = router.listdir(zip_archive.parent)
    assert any(i.name == zip_archive.name for i in items)


def test_write_through_archive_raises(zip_archive: Path, tmp_path: Path) -> None:
    router = VFSRouter()
    with pytest.raises(NotImplementedError):
        router.copy(zip_archive / "inside.txt", tmp_path / "out.txt")


def test_exists_inside_archive(zip_archive: Path) -> None:
    router = VFSRouter()
    assert router.exists(zip_archive / "inside.txt") is True
    assert router.exists(zip_archive / "ghost.txt") is False


def test_stat_inside_archive(zip_archive: Path) -> None:
    router = VFSRouter()
    item = router.stat(zip_archive / "inside.txt")
    assert item.name == "inside.txt"
    assert item.is_dir is False
