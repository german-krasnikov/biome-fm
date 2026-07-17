"""Unit tests for HexPreviewProvider — no Qt."""
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.hex import HexPreviewProvider


@pytest.fixture()
def provider():
    return HexPreviewProvider()


def test_can_handle_binary_ext(provider):
    assert provider.can_handle(Path("program.exe"))
    assert provider.can_handle(Path("lib.so"))
    assert provider.can_handle(Path("data.bin"))


def test_can_handle_text_ext(provider):
    assert not provider.can_handle(Path("script.py"))
    assert not provider.can_handle(Path("index.js"))
    assert not provider.can_handle(Path("README.md"))


def test_can_handle_null_sniff(provider, tmp_path):
    f = tmp_path / "unknown.xyz"
    f.write_bytes(b"hello\x00world")
    assert provider.can_handle(f)


def test_can_handle_clean_text(provider, tmp_path):
    f = tmp_path / "data.xyz"
    f.write_bytes(b"just plain text no nulls here")
    assert not provider.can_handle(f)


def test_can_handle_oserror(provider):
    assert not provider.can_handle(Path("/nonexistent/path/file.xyz"))


def test_render_hex_format(provider, tmp_path):
    data = bytes(range(32))
    f = tmp_path / "sample.bin"
    f.write_bytes(data)
    result = provider.render(PreviewRequest(path=f))
    assert result.kind == ContentKind.HTML
    assert "00000000" in result.data  # offset
    assert "monospace" in result.data
    # first byte 0x00
    assert "00" in result.data
    # ASCII column
    assert "|" in result.data


def test_render_truncation(provider, tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"\x00" * 5000)
    result = provider.render(PreviewRequest(path=f))
    assert result.kind == ContentKind.HTML
    assert "truncated" in result.data


def test_render_oserror(provider, tmp_path):
    result = provider.render(PreviewRequest(path=tmp_path / "missing.bin"))
    assert result.kind == ContentKind.ERROR
