"""Git blame preview provider — shows per-line authorship."""
from __future__ import annotations

import html
import subprocess
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.preview.providers._git_helpers import find_repo


class GitBlamePreviewProvider:
    priority = 2

    def can_handle(self, path: Path) -> bool:
        return find_repo(path) is not None

    def render(self, req: PreviewRequest) -> PreviewResult:
        repo = find_repo(req.path)
        if repo is None:
            return PreviewResult(kind=ContentKind.TEXT, data="Not in a git repository")
        try:
            r = subprocess.run(
                ["git", "blame", "--porcelain", str(req.path)],
                cwd=repo, capture_output=True, text=True, timeout=10,
            )
            return PreviewResult(kind=ContentKind.HTML, data=self._parse_to_html(r.stdout))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return PreviewResult(kind=ContentKind.TEXT, data="(git not available)")

    @staticmethod
    def _parse_to_html(blame: str) -> str:
        rows: list[str] = []
        commit = author = ""
        for line in blame.splitlines():
            if line.startswith("\t"):
                code = html.escape(line[1:])
                rows.append(f"<tr><td style='color:#888'>{html.escape(commit[:7])}</td>"
                            f"<td style='color:#aaa;padding:0 8px'>{html.escape(author)}</td>"
                            f"<td style='font-family:monospace'>{code}</td></tr>")
            elif line.startswith("author "):
                author = line[7:]
            elif len(line) >= 40 and all(c in "0123456789abcdef" for c in line[:40]):
                commit = line[:40]
        body = "\n".join(rows)
        return (
            "<style>table{border-collapse:collapse;font-size:12px;width:100%}"
            "td{padding:1px 4px;white-space:pre}</style>"
            f"<table>{body}</table>"
        )
