"""Git log preview provider — shows commit history for a file."""
from __future__ import annotations

import subprocess
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.preview.providers._git_helpers import find_repo


class GitLogPreviewProvider:
    priority = 2

    def can_handle(self, path: Path) -> bool:
        return find_repo(path) is not None

    def render(self, req: PreviewRequest) -> PreviewResult:
        repo = find_repo(req.path)
        if repo is None:
            return PreviewResult(kind=ContentKind.TEXT, data="Not in a git repository")
        try:
            r = subprocess.run(
                ["git", "log", "--oneline", "-50", "--", str(req.path)],
                cwd=repo, capture_output=True, text=True, timeout=5,
            )
            log = r.stdout or "(no commits for this file)"
            return PreviewResult(kind=ContentKind.HTML, data=self._to_html(log))
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return PreviewResult(kind=ContentKind.TEXT, data="(git not available)")

    @staticmethod
    def _to_html(log: str) -> str:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import TextLexer
        fmt = HtmlFormatter(nowrap=False, style="monokai")
        css = fmt.get_style_defs(".highlight")
        html = highlight(log, TextLexer(), fmt)
        return f"<style>{css}</style>{html}"
