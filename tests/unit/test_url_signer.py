"""Unit tests for url_signer — pure Python, no Qt."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.url_signer import sign_url


def _vfs_with_fs(**kwargs):
    vfs = MagicMock()
    vfs._fs = MagicMock(**kwargs)
    return vfs


def test_sign_url_fsspec():
    vfs = _vfs_with_fs()
    vfs._fs.sign.return_value = "https://s3.example.com/file?sig=abc"
    assert sign_url(Path("/bucket/file.txt"), vfs) == "https://s3.example.com/file?sig=abc"
    vfs._fs.sign.assert_called_once_with("/bucket/file.txt", expiration=3600)


def test_sign_url_fsspec_no_sign():
    vfs = _vfs_with_fs(spec=[])  # no sign attribute
    del vfs._fs.sign  # ensure hasattr returns False
    assert sign_url(Path("/bucket/file.txt"), vfs) is None


def test_sign_url_fsspec_exception():
    vfs = _vfs_with_fs()
    vfs._fs.sign.side_effect = Exception("network error")
    assert sign_url(Path("/bucket/file.txt"), vfs) is None


def test_sign_url_rclone(monkeypatch):
    class RcloneVFS:
        _remote = "s3:"

    vfs = RcloneVFS()
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="https://link.example.com/file\n", stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: result)
    assert sign_url(Path("/myfile.txt"), vfs) == "https://link.example.com/file"


def test_sign_url_unknown_vfs():
    assert sign_url(Path("/some/file.txt"), object()) is None
