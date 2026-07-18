"""Masked preview provider for .env files (F058)."""
from __future__ import annotations

import re
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MASK = re.compile(r"(?m)^(\s*(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=)(.+)$")


class EnvFileProvider:
    priority = 8

    def can_handle(self, path: Path) -> bool:
        return path.name == ".env" or path.name.startswith(".env.")

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            content = req.path.read_text(errors="replace")
            return PreviewResult(
                kind=ContentKind.TEXT,
                data=_MASK.sub(r"\1***", content),
                title=req.path.name,
            )
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
