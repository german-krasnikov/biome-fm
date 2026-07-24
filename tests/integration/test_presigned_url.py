"""Integration tests for Copy Presigned URL action."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock


from biome_fm.models.url_signer import can_sign_url, sign_url
from biome_fm.qt import QApplication


def _vfs_with_sign(url: str | None):
    vfs = MagicMock()
    vfs._fs = MagicMock()
    vfs._fs.sign.return_value = url
    return vfs


def _dispatch_presigned(path: Path, vfs: object) -> str | None:
    """Mirrors the presigned_url branch in app.py _dispatch."""
    url = sign_url(path, vfs)
    if url:
        QApplication.clipboard().setText(url)
    return url


def test_presigned_url_sets_clipboard(qtbot):
    vfs = _vfs_with_sign("https://s3.example.com/file?sig=abc")
    result = _dispatch_presigned(Path("/bucket/file.txt"), vfs)
    assert result == "https://s3.example.com/file?sig=abc"
    assert QApplication.clipboard().text() == "https://s3.example.com/file?sig=abc"


def test_presigned_url_none_leaves_clipboard(qtbot):
    QApplication.clipboard().setText("previous")
    vfs = _vfs_with_sign(None)
    vfs._fs.sign.return_value = None
    # sign attribute exists but returns None — simulate network error via exception
    vfs._fs.sign.side_effect = Exception("network error")
    result = _dispatch_presigned(Path("/bucket/file.txt"), vfs)
    assert result is None
    # clipboard must not be overwritten when sign fails
    assert QApplication.clipboard().text() == "previous"


def test_can_sign_url_guards_menu():
    """Menu item only shown for VFS backends that support signing."""
    assert can_sign_url(_vfs_with_sign("https://example.com")) is True
    assert can_sign_url(object()) is False
