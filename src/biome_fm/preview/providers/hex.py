"""Hex dump preview provider for binary files."""
from __future__ import annotations

from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_BYTES = 4096

_BINARY_EXTS = frozenset({
    ".exe", ".dll", ".so", ".dylib", ".o", ".a", ".pyc", ".pyd",
    ".bin", ".dat", ".db", ".sqlite", ".class", ".jar", ".wasm",
    ".dmg", ".iso", ".img",
})

_TEXT_EXTS = frozenset({
    ".py", ".js", ".ts", ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb",
    ".txt", ".md", ".rst", ".json", ".yaml", ".yml", ".toml", ".xml",
    ".html", ".css", ".sh", ".bat", ".cfg", ".ini", ".csv", ".log",
    ".sql", ".lua", ".pl", ".r", ".swift", ".kt", ".scala", ".hs",
    ".ex", ".exs", ".clj", ".lisp", ".el", ".vim", ".dockerfile", ".makefile",
})


class HexPreviewProvider:
    priority = 9

    def can_handle(self, path: Path) -> bool:
        sfx = path.suffix.lower()
        if sfx in _BINARY_EXTS:
            return True
        if sfx in _TEXT_EXTS:
            return False
        try:
            with path.open("rb") as f:
                chunk = f.read(512)
            return b"\x00" in chunk
        except OSError:
            return False

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            with req.path.open("rb") as f:
                data = f.read(_MAX_BYTES)
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        lines = []
        for offset in range(0, len(data), 16):
            row = data[offset : offset + 16]
            hex_part = " ".join(f"{b:02x}" for b in row)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
            lines.append(f"{offset:08x}  {hex_part:<48s}  |{ascii_part}|")

        if len(data) == _MAX_BYTES:
            lines.append(f"\n... truncated at {_MAX_BYTES} bytes")

        html = (
            "<pre style='font-family:monospace;font-size:12px;'>\n"
            + "\n".join(lines)
            + "\n</pre>"
        )
        return PreviewResult(kind=ContentKind.HTML, data=html)
