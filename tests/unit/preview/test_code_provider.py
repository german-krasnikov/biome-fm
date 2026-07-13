"""Unit tests for CodePreviewProvider."""
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.code import CodePreviewProvider


@pytest.fixture
def provider():
    return CodePreviewProvider()


def test_can_handle_python(provider):
    assert provider.can_handle(Path("script.py"))

def test_can_handle_javascript(provider):
    assert provider.can_handle(Path("app.js"))

def test_can_handle_c(provider):
    assert provider.can_handle(Path("main.c"))

def test_cannot_handle_txt(provider):
    assert not provider.can_handle(Path("readme.txt"))

def test_cannot_handle_unknown(provider):
    assert not provider.can_handle(Path("file.zzz_unknown"))

def test_render_returns_html(provider, tmp_path):
    f = tmp_path / "test.py"
    f.write_text("def hello(): pass\n")
    result = provider.render(PreviewRequest(path=f, dark=True))
    assert result.kind == ContentKind.HTML
    assert "<span" in result.data

def test_dark_vs_light(provider, tmp_path):
    f = tmp_path / "test.js"
    f.write_text("const x = 1;\n")
    dark = provider.render(PreviewRequest(path=f, dark=True)).data
    light = provider.render(PreviewRequest(path=f, dark=False)).data
    assert dark != light

def test_large_file_truncated(provider, tmp_path):
    f = tmp_path / "big.py"
    f.write_text("x = 1\n" * 100_000)
    result = provider.render(PreviewRequest(path=f, dark=True))
    assert "truncated" in result.data

def test_title_includes_line_count(provider, tmp_path):
    f = tmp_path / "small.py"
    f.write_text("a = 1\nb = 2\nc = 3\n")
    result = provider.render(PreviewRequest(path=f, dark=True))
    assert "3 lines" in result.title

def test_unreadable_file(provider):
    result = provider.render(PreviewRequest(path=Path("/nonexistent/x.py"), dark=True))
    assert result.kind == ContentKind.ERROR

def test_priority_lower_than_text(provider):
    from biome_fm.preview.providers.text import TextPreviewProvider
    assert provider.priority < TextPreviewProvider().priority
