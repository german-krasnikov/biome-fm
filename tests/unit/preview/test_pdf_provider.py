"""Unit tests for PDFPreviewProvider — no Qt, no real PDF files."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.preview.providers.pdf import PDFPreviewProvider


@pytest.fixture
def provider():
    return PDFPreviewProvider()


@pytest.fixture
def req(tmp_path):
    p = tmp_path / "test.pdf"
    p.touch()
    return PreviewRequest(path=p)


# --- can_handle ---

def test_can_handle_pdf(provider, tmp_path):
    assert provider.can_handle(tmp_path / "doc.pdf") is True


def test_can_handle_PDF_uppercase(provider, tmp_path):
    assert provider.can_handle(tmp_path / "doc.PDF") is True


def test_can_handle_txt(provider, tmp_path):
    assert provider.can_handle(tmp_path / "doc.txt") is False


# --- render: no deps ---

def test_render_no_deps(provider, req):
    """Both fitz and pdftotext unavailable → ERROR with install hint."""
    with patch.dict("sys.modules", {"fitz": None}):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = provider.render(req)

    assert result.kind == ContentKind.ERROR
    assert "pymupdf" in result.data
    assert "pdftotext" in result.data


# --- render: fitz available ---

def test_render_with_fitz(provider, req):
    """Mocked fitz returns page text → TEXT result."""
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Hello PDF"

    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_doc.__getitem__ = lambda self, i: mock_page

    mock_fitz = MagicMock()
    mock_fitz.open.return_value = mock_doc

    with patch.dict("sys.modules", {"fitz": mock_fitz}):
        result = provider.render(req)

    assert result.kind == ContentKind.TEXT
    assert "Hello PDF" in result.data


# --- render: pdftotext available ---

def test_render_with_pdftotext(provider, req):
    """fitz missing, pdftotext succeeds → TEXT result."""
    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = "Page one text\n"

    with patch.dict("sys.modules", {"fitz": None}):
        with patch("subprocess.run", return_value=fake_proc) as mock_run:
            result = provider.render(req)

    assert result.kind == ContentKind.TEXT
    assert "Page one text" in result.data
    # verify -l 10 and "-" (stdout) are in the call
    call_args = mock_run.call_args[0][0]
    assert "-l" in call_args
    assert "-" in call_args


# --- priority ---

def test_priority(provider):
    assert provider.priority == 4
