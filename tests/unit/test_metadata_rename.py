"""TDD: F428 — Multi-Rename Metadata Fields (EXIF/MP3)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.metadata_reader import read_metadata
from biome_fm.presenters.rename_template import expand_template


# ---------------------------------------------------------------------------
# metadata_reader tests
# ---------------------------------------------------------------------------


def test_read_metadata_non_media_file(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("hello")
    assert read_metadata(f) == {}


def test_read_metadata_no_piexif(tmp_path, monkeypatch):
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"\xff\xd8")
    monkeypatch.setitem(sys.modules, "piexif", None)
    assert read_metadata(f) == {}


def test_read_metadata_no_mutagen(tmp_path, monkeypatch):
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00" * 16)
    monkeypatch.setitem(sys.modules, "mutagen", None)
    assert read_metadata(f) == {}


def test_read_audio_mock(tmp_path, monkeypatch):
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00" * 16)

    mock_file = MagicMock()
    mock_file.get.side_effect = lambda key, default=None: {
        "artist": ["Beatles"],
        "title": ["Yesterday"],
        "album": ["Help!"],
        "date": ["1965"],
    }.get(key, default)

    mock_mutagen = MagicMock()
    mock_mutagen.File.return_value = mock_file
    monkeypatch.setitem(sys.modules, "mutagen", mock_mutagen)

    result = read_metadata(f)
    assert result["artist"] == "Beatles"
    assert result["title"] == "Yesterday"
    assert result["album"] == "Help!"
    assert result["year"] == "1965"


# ---------------------------------------------------------------------------
# expand_template META token tests
# ---------------------------------------------------------------------------


def test_expand_meta_token(tmp_path):
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00")
    result = expand_template("[META:artist] - [N]", f, 0, metadata={"artist": "Beatles"})
    assert "Beatles" in result
    assert "song" in result


def test_expand_meta_missing_key(tmp_path):
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00")
    result = expand_template("[META:unknown]", f, 0, metadata={"artist": "Beatles"})
    assert result == "[META:unknown]"


def test_expand_meta_none(tmp_path):
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00")
    result = expand_template("[META:artist]", f, 0, metadata=None)
    assert result == "[META:artist]"


def test_expand_meta_with_existing_tokens(tmp_path):
    f = tmp_path / "track.mp3"
    f.write_bytes(b"\x00")
    result = expand_template("[META:artist] - [N] - [C]", f, 0, metadata={"artist": "Beatles"})
    assert result.startswith("Beatles - track - ")
    assert result.endswith("001")
