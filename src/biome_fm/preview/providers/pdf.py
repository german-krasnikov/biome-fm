"""PDF preview provider — tries pymupdf (fitz), then pdftotext CLI."""
from __future__ import annotations

import subprocess
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_TEXT = 50_000


class PDFPreviewProvider:
    priority = 4

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def render(self, req: PreviewRequest) -> PreviewResult:
        # Try pymupdf first
        try:
            import fitz  # type: ignore[import]
            doc = fitz.open(req.path)
            pages = min(len(doc), 10)
            text = "\n\n".join(doc[i].get_text() for i in range(pages))
            doc.close()
            if len(text) > _MAX_TEXT:
                text = text[:_MAX_TEXT] + "\n\n... truncated"
            return PreviewResult(kind=ContentKind.TEXT, data=text or "(empty PDF)")
        except ImportError:
            pass
        except Exception:
            pass

        # Try pdftotext CLI (poppler-utils)
        try:
            result = subprocess.run(
                ["pdftotext", "-l", "10", str(req.path), "-"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                text = result.stdout[:_MAX_TEXT]
                if len(result.stdout) > _MAX_TEXT:
                    text += "\n\n... truncated"
                return PreviewResult(kind=ContentKind.TEXT, data=text)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return PreviewResult(
            kind=ContentKind.ERROR,
            data="PDF preview requires pymupdf (pip install pymupdf) or pdftotext (poppler-utils)",
        )
