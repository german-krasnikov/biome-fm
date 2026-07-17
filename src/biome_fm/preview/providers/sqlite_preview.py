"""SQLite/DuckDB preview provider."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_EXTS = frozenset({".db", ".sqlite", ".sqlite3"})
_TABLE_LIMIT = 5
_ROW_LIMIT = 20


class SqlitePreviewProvider:
    priority = 5

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _EXTS

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            conn = sqlite3.connect(f"file:{req.path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            parts: list[str] = []
            for tbl in tables[:_TABLE_LIMIT]:
                cursor.execute(f"SELECT * FROM [{tbl}] LIMIT {_ROW_LIMIT}")
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                thead = "".join(f"<th>{c}</th>" for c in cols)
                tbody = "".join(
                    "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
                    for row in rows
                )
                parts.append(
                    f"<h3>{tbl}</h3>"
                    f"<table border='1' cellpadding='3'>"
                    f"<thead><tr>{thead}</tr></thead>"
                    f"<tbody>{tbody}</tbody></table>"
                )
            conn.close()

            html = (
                "<html><body style='font-family:monospace;font-size:12px'>"
                + ("\n".join(parts) if parts else "<p>No tables found.</p>")
                + "</body></html>"
            )
            return PreviewResult(kind=ContentKind.HTML, data=html, title=req.path.name)
        except Exception as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))
