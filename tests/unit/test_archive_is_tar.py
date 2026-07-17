"""TDD: _is_tar must recognise all tar compression variants."""
from pathlib import Path

from biome_fm.models.archive_vfs import _is_tar


def test_is_tar_bare():
    assert _is_tar(Path("a.tar"))


def test_is_tar_gz():
    assert _is_tar(Path("a.tar.gz"))


def test_is_tar_bz2():
    assert _is_tar(Path("a.tar.bz2"))


def test_is_tar_xz():
    assert _is_tar(Path("a.tar.xz"))


def test_not_tar_zip():
    assert not _is_tar(Path("a.zip"))


def test_not_tar_single_gz():
    assert not _is_tar(Path("a.gz"))


def test_not_tar_bz2_alone():
    assert not _is_tar(Path("a.bz2"))
