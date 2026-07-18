"""CSV/TSV sortable table preview provider."""
from __future__ import annotations

import csv
import html
import io
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_BYTES = 10 * 1024 * 1024
_ROW_LIMIT = 50
_CSS = (
    "<style>table{border-collapse:collapse;font-size:13px;width:100%}"
    "th,td{border:1px solid #555;padding:4px 8px;text-align:left}"
    "thead{background:#2a2a2a;color:#ddd}"
    "tr:nth-child(even){background:#1e1e1e}tr:nth-child(odd){background:#252525}"
    "</style>"
)


def _detect_delim(sample: str) -> str:
    for delim in (",", ";", "\t"):
        if delim in sample:
            return delim
    return ","


class CsvTableProvider:
    priority = 6

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".csv", ".tsv"}

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            raw = req.path.read_bytes()
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        if len(raw) > _MAX_BYTES:
            return PreviewResult(kind=ContentKind.ERROR, data="File too large (>10 MB)")

        text = raw.decode("utf-8", errors="replace")
        if not text.strip():
            return PreviewResult(kind=ContentKind.ERROR, data="Empty file", title=req.path.name)

        delim = _detect_delim(text[:4096])
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))

        header, body = rows[0], rows[1:]
        extra = max(0, len(body) - _ROW_LIMIT)
        body = body[:_ROW_LIMIT]

        e = html.escape
        th = "".join(f"<th>{e(h)}</th>" for h in header)
        trs = "".join(
            "<tr>" + "".join(f"<td>{e(c)}</td>" for c in row) + "</tr>"
            for row in body
        )
        note = f"<p><i>…{extra} more rows not shown</i></p>" if extra else ""
        out = f"{_CSS}<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>{note}"
        return PreviewResult(kind=ContentKind.HTML, data=out, title=req.path.name)
