"""Unit tests for OfficeProvider — no real Office files, deps mocked."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest


@pytest.fixture
def provider():
    from biome_fm.preview.providers.office import OfficeProvider
    return OfficeProvider()


def req(path: Path) -> PreviewRequest:
    return PreviewRequest(path=path, dark=False)


# --- can_handle ---

def test_can_handle_docx(provider, tmp_path):
    assert provider.can_handle(tmp_path / "file.docx")

def test_can_handle_xlsx(provider, tmp_path):
    assert provider.can_handle(tmp_path / "file.xlsx")

def test_can_handle_pptx(provider, tmp_path):
    assert provider.can_handle(tmp_path / "file.pptx")

def test_txt_not_handled(provider, tmp_path):
    assert not provider.can_handle(tmp_path / "file.txt")


# --- missing dep → ERROR ---

def test_missing_dep_returns_error(provider, tmp_path):
    f = tmp_path / "doc.docx"
    f.write_bytes(b"fake")

    with patch.dict(sys.modules, {"docx": None}):
        result = provider.render(req(f))

    assert result.kind == ContentKind.ERROR
    assert result.data  # some message


# --- docx renders paragraphs ---

def test_docx_renders_paragraphs(provider, tmp_path):
    f = tmp_path / "doc.docx"
    f.write_bytes(b"fake")

    mock_para = MagicMock()
    mock_para.text = "Hello world"
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para]

    mock_docx_mod = MagicMock()
    mock_docx_mod.Document.return_value = mock_doc

    with patch.dict(sys.modules, {"docx": mock_docx_mod}):
        result = provider.render(req(f))

    assert result.kind == ContentKind.HTML
    assert "Hello world" in result.data
