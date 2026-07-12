"""Fallback provider — shows file metadata for any file type."""
from __future__ import annotations

import time
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult


class FallbackProvider:
    priority = 999

    def can_handle(self, path: Path) -> bool:
        return True

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            s = req.path.stat()
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(s.st_mtime))
            html = (
                f"<p><b>{req.path.name}</b></p>"
                f"<p>Size: {s.st_size:,} bytes<br>"
                f"Modified: {mtime}<br>"
                f"Type: {req.path.suffix or 'unknown'}</p>"
            )
            return PreviewResult(kind=ContentKind.HTML, data=html, title=req.path.name)
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
