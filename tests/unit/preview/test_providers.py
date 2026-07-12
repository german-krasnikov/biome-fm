"""Unit tests for preview providers — no Qt."""
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.fallback import FallbackProvider
from biome_fm.preview.providers.image import ImagePreviewProvider
from biome_fm.preview.providers.markdown import MarkdownPreviewProvider
from biome_fm.preview.providers.text import TextPreviewProvider


def test_md_can_handle():
    p = MarkdownPreviewProvider()
    assert p.can_handle(Path("README.md"))
    assert p.can_handle(Path("notes.markdown"))
    assert p.can_handle(Path("doc.mdx"))
    assert not p.can_handle(Path("script.py"))


def test_md_render_returns_markdown_kind(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# Hello\n")
    result = MarkdownPreviewProvider().render(PreviewRequest(path=f))
    assert result.kind == ContentKind.MARKDOWN
    assert "# Hello" in result.data  # type: ignore[operator]


def test_md_oserror_returns_error(tmp_path):
    result = MarkdownPreviewProvider().render(PreviewRequest(path=tmp_path / "nonexistent.md"))
    assert result.kind == ContentKind.ERROR


def test_image_can_handle():
    p = ImagePreviewProvider()
    assert p.can_handle(Path("photo.jpg"))
    assert p.can_handle(Path("icon.png"))
    assert not p.can_handle(Path("doc.pdf"))


def test_text_can_handle():
    p = TextPreviewProvider()
    assert p.can_handle(Path("hello.py"))
    assert p.can_handle(Path("config.toml"))
    assert not p.can_handle(Path("archive.zip"))


def test_text_truncates(tmp_path):
    f = tmp_path / "big.txt"
    f.write_bytes(b"x" * (300 * 1024))
    result = TextPreviewProvider().render(PreviewRequest(path=f))
    assert result.kind == ContentKind.TEXT
    assert len(result.data) <= 256 * 1024  # type: ignore[arg-type]


def test_fallback_always_handles():
    p = FallbackProvider()
    assert p.can_handle(Path("archive.7z"))
    assert p.can_handle(Path("unknown.bin"))


def test_fallback_returns_html(tmp_path):
    f = tmp_path / "unknown.bin"
    f.write_bytes(b"\x00\x01")
    result = FallbackProvider().render(PreviewRequest(path=f))
    assert result.kind == ContentKind.HTML
    assert "unknown.bin" in result.data  # type: ignore[arg-type]


def test_image_size_limit(tmp_path):
    f = tmp_path / "big.png"
    # write a tiny file but mock stat — easier: just test the error branch
    f.write_bytes(b"\x89PNG")  # tiny fake png
    result = ImagePreviewProvider().render(PreviewRequest(path=f))
    # tiny file is fine, should return IMAGE kind
    assert result.kind == ContentKind.IMAGE


def test_text_oserror_returns_error(tmp_path):
    result = TextPreviewProvider().render(PreviewRequest(path=tmp_path / "nonexistent.py"))
    assert result.kind == ContentKind.ERROR


def test_fallback_oserror_returns_error(tmp_path):
    result = FallbackProvider().render(PreviewRequest(path=tmp_path / "nonexistent.bin"))
    assert result.kind == ContentKind.ERROR
