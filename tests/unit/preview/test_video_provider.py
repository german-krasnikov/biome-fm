import subprocess
from pathlib import Path
from unittest.mock import patch

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.video import VideoPreviewProvider


def test_can_handle_mp4_with_ffmpeg():
    prov = VideoPreviewProvider()
    with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
        assert prov.can_handle(Path("video.mp4"))


def test_cannot_handle_without_ffmpeg():
    prov = VideoPreviewProvider()
    with patch("shutil.which", return_value=None):
        assert not prov.can_handle(Path("video.mp4"))


def test_cannot_handle_txt():
    prov = VideoPreviewProvider()
    assert not prov.can_handle(Path("readme.txt"))


def test_render_success():
    prov = VideoPreviewProvider()
    req = PreviewRequest(path=Path("test.mp4"))
    with patch("biome_fm.preview.providers.video.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"PNG_DATA"
        result = prov.render(req)
    assert result.kind == ContentKind.IMAGE
    assert result.data == b"PNG_DATA"


def test_render_failure():
    prov = VideoPreviewProvider()
    req = PreviewRequest(path=Path("test.mp4"))
    with patch("biome_fm.preview.providers.video.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = b""
        result = prov.render(req)
    assert result.kind == ContentKind.ERROR


def test_render_timeout():
    prov = VideoPreviewProvider()
    req = PreviewRequest(path=Path("test.mp4"))
    with patch(
        "biome_fm.preview.providers.video.subprocess.run",
        side_effect=subprocess.TimeoutExpired("ffmpeg", 10),
    ):
        result = prov.render(req)
    assert result.kind == ContentKind.ERROR
