"""Tests for ArchiveVFS — zip and tar.gz read-only VFS."""
from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from biome_fm.models.archive_vfs import ArchiveVFS


@pytest.fixture
def zip_archive(tmp_path: Path) -> Path:
    archive = tmp_path / "test.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("file1.txt", "hello")
        zf.writestr("file2.py", "print('hi')")
        zf.writestr("sub/nested.txt", "deep")
        zf.writestr("sub/deep/bottom.log", "log")
    return archive


@pytest.fixture
def tar_archive(tmp_path: Path) -> Path:
    archive = tmp_path / "test.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for name, content in [
            ("file1.txt", b"hello"),
            ("file2.py", b"print('hi')"),
            ("sub/nested.txt", b"deep"),
            ("sub/deep/bottom.log", b"log"),
        ]:
            buf = io.BytesIO(content)
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, buf)
    return archive


def test_listdir_zip_root(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    items = vfs.listdir(zip_archive)
    names = {i.name for i in items}
    assert names == {"file1.txt", "file2.py", "sub"}
    sub = next(i for i in items if i.name == "sub")
    assert sub.is_dir is True


def test_listdir_zip_subdir(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    items = vfs.listdir(zip_archive / "sub")
    names = {i.name for i in items}
    assert names == {"nested.txt", "deep"}
    deep = next(i for i in items if i.name == "deep")
    assert deep.is_dir is True


def test_nested_subdir(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    items = vfs.listdir(zip_archive / "sub" / "deep")
    names = {i.name for i in items}
    assert names == {"bottom.log"}


def test_listdir_tar_root(tar_archive: Path) -> None:
    vfs = ArchiveVFS(tar_archive)
    items = vfs.listdir(tar_archive)
    names = {i.name for i in items}
    assert names == {"file1.txt", "file2.py", "sub"}
    sub = next(i for i in items if i.name == "sub")
    assert sub.is_dir is True


def test_listdir_tar_subdir(tar_archive: Path) -> None:
    vfs = ArchiveVFS(tar_archive)
    items = vfs.listdir(tar_archive / "sub")
    names = {i.name for i in items}
    assert names == {"nested.txt", "deep"}


def test_stat_zip_file(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    item = vfs.stat(zip_archive / "file1.txt")
    assert item.name == "file1.txt"
    assert item.size == 5  # len("hello")
    assert item.is_dir is False


def test_stat_zip_dir_implicit(zip_archive: Path) -> None:
    """sub/ has no explicit entry in the zip — virtual dir."""
    vfs = ArchiveVFS(zip_archive)
    item = vfs.stat(zip_archive / "sub")
    assert item.name == "sub"
    assert item.is_dir is True


def test_exists_true_and_false(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    assert vfs.exists(zip_archive / "file1.txt") is True
    assert vfs.exists(zip_archive / "nonexistent.txt") is False


def test_exists_virtual_dir(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    assert vfs.exists(zip_archive / "sub") is True


def test_write_ops_raise(zip_archive: Path) -> None:
    vfs = ArchiveVFS(zip_archive)
    with pytest.raises(NotImplementedError):
        vfs.copy(zip_archive / "file1.txt", zip_archive / "file3.txt")
    with pytest.raises(NotImplementedError):
        vfs.move(zip_archive / "file1.txt", zip_archive / "file3.txt")
    with pytest.raises(NotImplementedError):
        vfs.delete(zip_archive / "file1.txt")
    with pytest.raises(NotImplementedError):
        vfs.mkdir(zip_archive / "newdir")


def test_empty_dir_in_zip(tmp_path: Path) -> None:
    archive = tmp_path / "empty_dir.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(zipfile.ZipInfo("emptydir/"), "")
    vfs = ArchiveVFS(archive)
    items = vfs.listdir(archive / "emptydir")
    assert items == []


def test_zip_slip_filtered(tmp_path: Path) -> None:
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(zipfile.ZipInfo("../escape.txt"), "evil")
        zf.writestr("safe.txt", "ok")
    vfs = ArchiveVFS(archive)
    items = vfs.listdir(archive)
    assert all(i.name != ".." for i in items)
    assert any(i.name == "safe.txt" for i in items)


def test_tar_slip_filtered(tmp_path: Path) -> None:
    archive = tmp_path / "evil.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 4
        tf.addfile(info, io.BytesIO(b"evil"))
        info2 = tarfile.TarInfo("safe.txt")
        info2.size = 2
        tf.addfile(info2, io.BytesIO(b"ok"))
    vfs = ArchiveVFS(archive)
    items = vfs.listdir(archive)
    assert all(i.name != ".." for i in items)
    assert any(i.name == "safe.txt" for i in items)
