"""Unit tests for mmap-based large-file preview reading."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.text import TextPreviewProvider, _MAX_BYTES


@pytest.fixture()
def provider() -> TextPreviewProvider:
    return TextPreviewProvider()


def _req(path: Path) -> PreviewRequest:
    return PreviewRequest(path=path)


def test_empty_file_no_crash(tmp_path: Path, provider: TextPreviewProvider) -> None:
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    result = provider.render(_req(f))
    assert result.kind == ContentKind.TEXT
    assert result.data == ""


def test_normal_file_unchanged(tmp_path: Path, provider: TextPreviewProvider) -> None:
    content = b"hello world\n"
    f = tmp_path / "small.py"
    f.write_bytes(content)
    result = provider.render(_req(f))
    assert result.kind == ContentKind.TEXT
    assert "hello world" in result.data


def test_large_file_preview_limited(tmp_path: Path, provider: TextPreviewProvider) -> None:
    f = tmp_path / "big.txt"
    # Write slightly more than _MAX_BYTES
    f.write_bytes(b"A" * (_MAX_BYTES + 4096))
    result = provider.render(_req(f))
    assert result.kind == ContentKind.TEXT
    # Must NOT return more than _MAX_BYTES worth of decoded content
    assert len(result.data.encode()) <= _MAX_BYTES


def test_binary_file_preview(tmp_path: Path, provider: TextPreviewProvider) -> None:
    f = tmp_path / "data.txt"
    f.write_bytes(bytes(range(256)) * 10)
    result = provider.render(_req(f))
    # Should not crash; kind is TEXT or ERROR but never raises
    assert result.kind in (ContentKind.TEXT, ContentKind.ERROR)
