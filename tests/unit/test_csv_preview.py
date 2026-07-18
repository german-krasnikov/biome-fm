"""Unit tests for CsvTableProvider."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.csv_preview import CsvTableProvider


@pytest.fixture
def provider():
    return CsvTableProvider()


@pytest.fixture
def tmp_csv(tmp_path):
    def _make(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _make


def req(path: Path) -> PreviewRequest:
    return PreviewRequest(path=path)


# --- can_handle ---

def test_can_handle_csv(provider, tmp_path):
    assert provider.can_handle(tmp_path / "data.csv")
    assert provider.can_handle(tmp_path / "data.CSV")

def test_can_handle_tsv(provider, tmp_path):
    assert provider.can_handle(tmp_path / "data.tsv")

def test_cannot_handle_txt(provider, tmp_path):
    assert not provider.can_handle(tmp_path / "data.txt")


# --- render ---

def test_render_csv_returns_html(provider, tmp_csv):
    p = tmp_csv("a.csv", "name,age\nAlice,30\nBob,25\n")
    result = provider.render(req(p))
    assert result.kind == ContentKind.HTML
    assert "<table" in result.data

def test_delimiter_detected_semicolon(provider, tmp_csv):
    p = tmp_csv("b.csv", "name;age\nAlice;30\n")
    result = provider.render(req(p))
    assert "Alice" in result.data
    assert "30" in result.data

def test_delimiter_detected_tab(provider, tmp_csv):
    p = tmp_csv("c.tsv", "name\tage\nAlice\t30\n")
    result = provider.render(req(p))
    assert "Alice" in result.data

def test_header_row_in_thead(provider, tmp_csv):
    p = tmp_csv("d.csv", "col1,col2\nv1,v2\n")
    result = provider.render(req(p))
    assert "<thead>" in result.data
    assert "<th>" in result.data or "<th " in result.data

def test_size_limit(provider, tmp_path):
    p = tmp_path / "big.csv"
    p.write_bytes(b"a,b\n" * (10 * 1024 * 1024 // 4 + 1))
    result = provider.render(req(p))
    assert result.kind == ContentKind.ERROR

def test_empty_file(provider, tmp_csv):
    p = tmp_csv("empty.csv", "")
    result = provider.render(req(p))
    assert result.kind in (ContentKind.ERROR, ContentKind.HTML)
    # should not crash; if HTML, still contains some message
    if result.kind == ContentKind.HTML:
        assert result.data  # non-empty

def test_row_limit_note(provider, tmp_csv):
    rows = "a,b\n" + "x,y\n" * 60
    p = tmp_csv("many.csv", rows)
    result = provider.render(req(p))
    assert "more" in result.data.lower()

def test_xss_escaped_in_header_and_cells(provider, tmp_csv):
    """User-controlled CSV content must never appear unescaped in HTML output."""
    p = tmp_csv("evil.csv", '<script>alert(1)</script>,safe\n<b>bold</b>,value\n')
    result = provider.render(req(p))
    assert result.kind == ContentKind.HTML
    assert "<script>" not in result.data
    assert "&lt;script&gt;" in result.data
    assert "<b>" not in result.data or "&lt;b&gt;" in result.data
