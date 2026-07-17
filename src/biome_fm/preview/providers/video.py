"""Video thumbnail via ffmpeg subprocess."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_VIDEO_EXTS = frozenset({".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"})


class VideoPreviewProvider:
    priority = 7

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _VIDEO_EXTS and bool(shutil.which("ffmpeg"))

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            r = subprocess.run(
                ["ffmpeg", "-i", str(req.path), "-ss", "00:00:01",
                 "-vframes", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                capture_output=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout:
                return PreviewResult(ContentKind.IMAGE, r.stdout, req.path.name)
        except Exception:
            pass
        return PreviewResult(ContentKind.ERROR, "ffmpeg failed or not available")
