"""Unit tests for encoding-aware content search (F045)."""
from __future__ import annotations

from unittest.mock import Mock

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchPresenter, _decode_content


def test_utf8_file_found():
    raw = "hello world".encode("utf-8")
    assert _decode_content(raw) == "hello world"


def test_latin1_file_found():
    raw = "café résumé".encode("latin-1")
    result = _decode_content(raw)
    assert result is not None
    assert "café" in result


def test_binary_file_skipped():
    # lots of null bytes — clearly binary
    raw = b"\x00\x01\x02\x03\x04" * 2000
    assert _decode_content(raw) is None


def test_windows_1252_not_rejected_as_binary():
    raw = b"Hello \x93world\x94"
    result = _decode_content(raw)
    assert result is not None
    assert "Hello" in result


def test_empty_file_no_crash():
    assert _decode_content(b"") == ""


def test_content_match_latin1_end_to_end(tmp_path):
    f = tmp_path / "note.txt"
    f.write_bytes("café résumé".encode("latin-1"))
    item = FileItem(name="note.txt", path=f, is_dir=False, size=f.stat().st_size, modified=0.0)
    presenter = SearchPresenter(vfs=Mock(), root=tmp_path)
    result = presenter._content_match(item, "café")
    assert result is not None
    assert result.item is item
