"""Image preview provider — reads raw bytes in background."""
from __future__ import annotations

from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".ico", ".svg"}
_MAX_BYTES = 50 * 1024 * 1024  # 50MB


class ImagePreviewProvider:
    priority = 0

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _IMAGE_EXT

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            size = req.path.stat().st_size
            if size > _MAX_BYTES:
                return PreviewResult(
                    kind=ContentKind.ERROR,
                    data=f"Image too large ({size // 1024 // 1024} MB)",
                )
            return PreviewResult(kind=ContentKind.IMAGE, data=req.path.read_bytes(), title=req.path.name)
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
