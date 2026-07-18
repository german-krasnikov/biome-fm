"""Jupyter Notebook preview provider."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_BYTES = 4 * 1024 * 1024  # 4 MB — notebooks are JSON, 4 MB is already huge

_CSS = """
body{font-family:monospace;font-size:13px;padding:8px;margin:0}
.code{background:#1e1e2e;color:#cdd6f4;padding:8px;border-radius:4px;margin:4px 0;white-space:pre-wrap;overflow-x:auto}
.markdown{padding:4px 8px;margin:4px 0;border-left:3px solid #89b4fa}
.output{background:#181825;color:#a6e3a1;padding:6px 8px;margin:2px 0 8px 0;white-space:pre-wrap;font-size:12px}
.raw{color:#9399b2;padding:4px 8px;margin:4px 0;white-space:pre-wrap}
"""


class NotebookProvider:
    priority = 4

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".ipynb"

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            raw = req.path.read_bytes()
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
        if len(raw) > _MAX_BYTES:
            return PreviewResult(kind=ContentKind.ERROR, data="File too large (>4 MB)")
        try:
            nb = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        parts: list[str] = []
        for cell in nb.get("cells", []):
            src = "".join(cell.get("source", []))
            if not src.strip():
                continue
            ct = cell.get("cell_type", "raw")
            if ct == "code":
                parts.append(f'<pre class="code">{escape(src)}</pre>')
                for out in cell.get("outputs", []):
                    text = "".join(out.get("text", []))
                    if text:
                        lines = text.splitlines()[:10]
                        parts.append(f'<pre class="output">{escape(chr(10).join(lines))}</pre>')
            elif ct == "markdown":
                parts.append(f'<div class="markdown">{escape(src)}</div>')
            else:
                parts.append(f'<pre class="raw">{escape(src)}</pre>')

        html = f"<style>{_CSS}</style>" + "\n".join(parts)
        return PreviewResult(kind=ContentKind.HTML, data=html, title=req.path.name)
