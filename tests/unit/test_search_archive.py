"""Tests: SearchPresenter + ArchiveVFS — search inside archives."""
from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from biome_fm.models.archive_vfs import ArchiveVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter


def make_zip(tmp_path: Path, files: dict[str, bytes]) -> Path:
    zpath = tmp_path / "test.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return zpath


def make_tar_gz(tmp_path: Path, files: dict[str, bytes]) -> Path:
    tpath = tmp_path / "test.tar.gz"
    with tarfile.open(tpath, "w:gz") as tf:
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    return tpath


def test_search_name_in_zip(tmp_path: Path) -> None:
    zpath = make_zip(tmp_path, {"hello.txt": b"world", "other.py": b"code"})
    vfs = ArchiveVFS(zpath)
    sp = SearchPresenter(vfs, zpath)
    results = sp.search("*.txt", SearchMode.NAME_WILDCARD)
    assert len(results) == 1
    assert results[0].item.name == "hello.txt"


def test_search_content_in_zip(tmp_path: Path) -> None:
    zpath = make_zip(tmp_path, {"hello.txt": b"hello world", "other.txt": b"nothing here"})
    vfs = ArchiveVFS(zpath)
    sp = SearchPresenter(vfs, zpath)
    results = sp.search("world", SearchMode.CONTENT)
    assert len(results) == 1
    assert results[0].item.name == "hello.txt"


def test_search_name_in_tar_gz(tmp_path: Path) -> None:
    tpath = make_tar_gz(tmp_path, {"readme.md": b"# Title", "data.csv": b"a,b,c"})
    vfs = ArchiveVFS(tpath)
    sp = SearchPresenter(vfs, tpath)
    results = sp.search("*.md", SearchMode.NAME_WILDCARD)
    assert len(results) == 1
    assert results[0].item.name == "readme.md"


def test_search_content_in_tar_gz(tmp_path: Path) -> None:
    tpath = make_tar_gz(tmp_path, {"doc.txt": b"find me inside tar", "other.txt": b"nope"})
    vfs = ArchiveVFS(tpath)
    sp = SearchPresenter(vfs, tpath)
    results = sp.search("find me", SearchMode.CONTENT)
    assert len(results) == 1
    assert results[0].item.name == "doc.txt"


def test_search_nested_dirs_in_archive(tmp_path: Path) -> None:
    zpath = make_zip(tmp_path, {"dir/sub/file.txt": b"nested", "top.txt": b"top"})
    vfs = ArchiveVFS(zpath)
    sp = SearchPresenter(vfs, zpath)
    results = sp.search("*.txt", SearchMode.NAME_WILDCARD)
    names = {r.item.name for r in results}
    assert "top.txt" in names
    assert "file.txt" in names


def test_search_binary_in_archive_skipped(tmp_path: Path) -> None:
    binary = bytes(range(256)) * 40  # 10KB of clearly binary data
    zpath = make_zip(tmp_path, {"binary.bin": binary, "text.txt": b"searchable content"})
    vfs = ArchiveVFS(zpath)
    sp = SearchPresenter(vfs, zpath)
    results = sp.search("searchable", SearchMode.CONTENT)
    assert len(results) == 1
    assert results[0].item.name == "text.txt"


def test_search_corrupt_archive_no_crash(tmp_path: Path) -> None:
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip at all, corrupt content!!!")
    vfs = ArchiveVFS(bad)
    sp = SearchPresenter(vfs, bad)
    results = sp.search("*", SearchMode.NAME_WILDCARD)
    assert results == []  # no crash, empty results


def test_search_large_archive_content_skipped(tmp_path: Path) -> None:
    """Archives >100MB raise OSError from read_bytes; SearchPresenter returns no results."""
    import unittest.mock as mock
    zpath = make_zip(tmp_path, {"big.txt": b"hello world"})
    vfs = ArchiveVFS(zpath)
    sp = SearchPresenter(vfs, zpath)
    with mock.patch.object(vfs, "read_bytes", side_effect=OSError("archive too large")):
        results = sp.search("hello", SearchMode.CONTENT)
    assert results == []
