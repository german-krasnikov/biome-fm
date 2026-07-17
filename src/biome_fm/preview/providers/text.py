"""Plain-text preview provider."""
from __future__ import annotations

from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.utils.encoding import decode_smart

_TEXT_EXT = {
    ".txt", ".py", ".js", ".ts", ".json", ".toml", ".yaml", ".yml",
    ".xml", ".html", ".css", ".sh", ".bash", ".zsh", ".rs", ".go",
    ".c", ".cpp", ".h", ".java", ".rb", ".php", ".rst", ".ini",
    ".cfg", ".conf", ".env", ".gitignore", ".dockerfile",
}
_MAX_BYTES = 256 * 1024


class TextPreviewProvider:
    priority = 10

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _TEXT_EXT

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            data = req.path.read_bytes()[:_MAX_BYTES]
            text, _ = decode_smart(data)
            return PreviewResult(kind=ContentKind.TEXT, data=text, title=req.path.name)
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
