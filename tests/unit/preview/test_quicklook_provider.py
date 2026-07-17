"""Tests for QuickLookProvider (macOS qlmanage fallback)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest


@pytest.fixture()
def provider():
    from biome_fm.preview.providers.quicklook import QuickLookProvider
    return QuickLookProvider()


# --- can_handle ---

def test_can_handle_non_darwin(provider, tmp_path):
    f = tmp_path / "test.xyz"
    f.write_bytes(b"x")
    with patch("sys.platform", "linux"):
        assert provider.can_handle(f) is False


def test_can_handle_darwin_file(provider, tmp_path):
    f = tmp_path / "test.xyz"
    f.write_bytes(b"x")
    with patch("sys.platform", "darwin"):
        assert provider.can_handle(f) is True


def test_can_handle_darwin_missing_file(provider, tmp_path):
    with patch("sys.platform", "darwin"):
        assert provider.can_handle(tmp_path / "nope.xyz") is False


# --- render ---

def _fake_run_with_png(tmp_dir_holder):
    """Returns a side_effect for subprocess.run that writes a PNG to the captured tmpdir."""
    def side_effect(cmd, **kwargs):
        # The temp dir is the -o argument
        out_dir = Path(cmd[cmd.index("-o") + 1])
        (out_dir / "preview.png").write_bytes(b"\x89PNG\r\n")
        return MagicMock(returncode=0)
    return side_effect


def test_render_success(provider, tmp_path):
    req = PreviewRequest(path=tmp_path / "file.xyz")

    def fake_run(cmd, **kwargs):
        out_dir = Path(cmd[cmd.index("-o") + 1])
        (out_dir / "preview.png").write_bytes(b"\x89PNG\r\n")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        result = provider.render(req)

    assert result.kind == ContentKind.IMAGE
    assert result.data == b"\x89PNG\r\n"


def test_render_no_thumbnail(provider, tmp_path):
    req = PreviewRequest(path=tmp_path / "file.xyz")

    with patch("subprocess.run", return_value=MagicMock(returncode=1)):
        result = provider.render(req)

    assert result.kind == ContentKind.ERROR
    assert "no thumbnail" in result.data


def test_render_timeout(provider, tmp_path):
    req = PreviewRequest(path=tmp_path / "file.xyz")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("qlmanage", 10)):
        result = provider.render(req)

    assert result.kind == ContentKind.ERROR
    assert "timed out" in result.data.lower()


def test_render_not_found(provider, tmp_path):
    req = PreviewRequest(path=tmp_path / "file.xyz")

    with patch("subprocess.run", side_effect=FileNotFoundError("qlmanage not found")):
        result = provider.render(req)

    assert result.kind == ContentKind.ERROR


def test_tmpdir_cleaned(provider, tmp_path):
    req = PreviewRequest(path=tmp_path / "file.xyz")
    created_dirs: list[Path] = []

    real_mkdtemp = tempfile.mkdtemp

    def capturing_mkdtemp():
        d = real_mkdtemp()
        created_dirs.append(Path(d))
        return d

    def fake_run(cmd, **kwargs):
        out_dir = Path(cmd[cmd.index("-o") + 1])
        (out_dir / "preview.png").write_bytes(b"\x89PNG\r\n")
        return MagicMock(returncode=0)

    with patch("tempfile.mkdtemp", side_effect=capturing_mkdtemp), \
         patch("subprocess.run", side_effect=fake_run):
        provider.render(req)

    assert created_dirs, "mkdtemp was not called"
    for d in created_dirs:
        assert not d.exists(), f"tmpdir {d} was not cleaned up"
