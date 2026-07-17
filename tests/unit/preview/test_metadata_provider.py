"""Tests for MetadataPreviewProvider (audio tags)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _provider():
    from biome_fm.preview.providers.metadata import MetadataPreviewProvider
    return MetadataPreviewProvider()


def _req(path: Path):
    from biome_fm.preview.provider import PreviewRequest
    return PreviewRequest(path=path)


# --- can_handle ---

def test_can_handle_mp3():
    assert _provider().can_handle(Path("song.mp3")) is True


def test_can_handle_flac():
    assert _provider().can_handle(Path("track.flac")) is True


def test_can_handle_jpg():
    assert _provider().can_handle(Path("photo.jpg")) is False


def test_can_handle_txt():
    assert _provider().can_handle(Path("readme.txt")) is False


# --- render ---

def test_render_without_mutagen(tmp_path):
    """No mutagen installed → falls back to stat info, no crash."""
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"\xff\xfb" * 100)

    # Remove mutagen from sys.modules if present, then block import
    saved = sys.modules.pop("mutagen", None)
    try:
        with patch.dict("sys.modules", {"mutagen": None}):
            result = _provider().render(_req(audio))
    finally:
        if saved is not None:
            sys.modules["mutagen"] = saved

    from biome_fm.preview.provider import ContentKind
    assert result.kind == ContentKind.HTML
    assert "bytes" in result.data or "Size" in result.data


def test_render_with_mutagen(tmp_path):
    """mutagen.File returns tags → HTML contains artist and title."""
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"\xff\xfb" * 100)

    mock_tags = {
        "title": ["My Song"],
        "artist": ["Test Artist"],
        "album": ["Best Album"],
    }
    mock_info = MagicMock()
    mock_info.length = 183.0
    mock_info.bitrate = 320000
    mock_info.sample_rate = 44100

    mock_file = MagicMock()
    mock_file.tags = mock_tags
    mock_file.info = mock_info

    mock_mutagen = MagicMock()
    mock_mutagen.File.return_value = mock_file

    with patch.dict("sys.modules", {"mutagen": mock_mutagen}):
        result = _provider().render(_req(audio))

    from biome_fm.preview.provider import ContentKind
    assert result.kind == ContentKind.HTML
    assert "Test Artist" in result.data
    assert "My Song" in result.data
