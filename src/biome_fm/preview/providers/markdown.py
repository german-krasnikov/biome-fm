"""Markdown preview provider."""
from __future__ import annotations

from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MD_EXT = {".md", ".markdown", ".mdx", ".mdown"}
_MAX_BYTES = 200_000


class MarkdownPreviewProvider:
    priority = 5

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _MD_EXT

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            raw = req.path.read_bytes()
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        text = raw[:_MAX_BYTES].decode("utf-8", errors="replace")
        if len(raw) > _MAX_BYTES:
            text += "\n\n*(truncated)*"

        return PreviewResult(kind=ContentKind.MARKDOWN, data=text, title=req.path.name)
