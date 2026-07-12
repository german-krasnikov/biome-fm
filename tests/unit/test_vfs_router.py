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


def test_tar_gz_treated_as_archive(tmp_path: Path) -> None:
    """Compound suffix .tar.gz must be found as archive root."""
    from biome_fm.models.vfs_router import _BUILTIN_EXTENSIONS, _find_archive_root

    tgz = tmp_path / "pkg.tar.gz"
    tgz.write_bytes(b"fake")
    assert _find_archive_root(tgz, _BUILTIN_EXTENSIONS) == tgz
    # Path inside should also resolve to the archive
    assert _find_archive_root(tgz / "readme.txt", _BUILTIN_EXTENSIONS) == tgz


def test_gz_not_treated_as_archive(tmp_path: Path) -> None:
    """Bare .gz (manpage, config) must NOT be dispatched to ArchiveVFS."""
    from biome_fm.models.vfs_router import _BUILTIN_EXTENSIONS, _find_archive_root

    gz = tmp_path / "page.1.gz"
    gz.write_bytes(b"fake gzip data")
    # The regression: old code matched "gz" suffix → archive root; new code must return None
    assert _find_archive_root(gz, _BUILTIN_EXTENSIONS) is None
    # Also verify via router: parent listing sees .gz as plain file
    router = VFSRouter()
    items = router.listdir(tmp_path)
    assert any(i.name == "page.1.gz" for i in items)
    assert len(router._cache) == 0
