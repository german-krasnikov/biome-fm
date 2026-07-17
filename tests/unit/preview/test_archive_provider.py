"""Tests for ArchivePreviewProvider — TDD Red phase."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.archive import ArchivePreviewProvider


@pytest.fixture
def provider() -> ArchivePreviewProvider:
    return ArchivePreviewProvider()


@pytest.fixture
def sample_zip(tmp_path: Path) -> Path:
    p = tmp_path / "sample.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("hello.txt", "hello world")
        zf.writestr("sub/world.py", "print('hi')")
    return p


@pytest.fixture
def sample_tar(tmp_path: Path) -> Path:
    p = tmp_path / "sample.tar.gz"
    src = tmp_path / "src"
    src.mkdir()
    (src / "foo.txt").write_text("foo")
    (src / "bar.py").write_text("bar")
    with tarfile.open(p, "w:gz") as tf:
        tf.add(src / "foo.txt", arcname="foo.txt")
        tf.add(src / "bar.py", arcname="bar.py")
    return p


# --- can_handle ---

def test_can_handle_zip(provider: ArchivePreviewProvider, tmp_path: Path) -> None:
    assert provider.can_handle(tmp_path / "archive.zip") is True


def test_can_handle_tar_gz(provider: ArchivePreviewProvider, tmp_path: Path) -> None:
    assert provider.can_handle(tmp_path / "archive.tar.gz") is True


def test_can_handle_tgz(provider: ArchivePreviewProvider, tmp_path: Path) -> None:
    assert provider.can_handle(tmp_path / "archive.tgz") is True


def test_can_handle_txt(provider: ArchivePreviewProvider, tmp_path: Path) -> None:
    assert provider.can_handle(tmp_path / "readme.txt") is False


# --- render ---

def test_render_zip_lists_files(provider: ArchivePreviewProvider, sample_zip: Path) -> None:
    result = provider.render(PreviewRequest(path=sample_zip))
    assert result.kind == ContentKind.HTML
    assert "hello.txt" in result.data
    assert "world.py" in result.data


def test_render_tar_lists_files(provider: ArchivePreviewProvider, sample_tar: Path) -> None:
    result = provider.render(PreviewRequest(path=sample_tar))
    assert result.kind == ContentKind.HTML
    assert "foo.txt" in result.data
    assert "bar.py" in result.data


def test_render_shows_total_count(provider: ArchivePreviewProvider, sample_zip: Path) -> None:
    result = provider.render(PreviewRequest(path=sample_zip))
    assert "2" in result.data  # 2 files in the zip
