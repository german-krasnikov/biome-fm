"""Git diff preview provider — shows colored diff for modified/staged files."""
from __future__ import annotations

import subprocess
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_BINARY_EXTS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav", ".flac",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".o", ".pyc",
})


class GitDiffPreviewProvider:
    priority = 3  # higher priority than code(8), only active for dirty files

    def __init__(self, status_fn=None) -> None:
        self._status_fn = status_fn

    def can_handle(self, path: Path) -> bool:
        if self._status_fn is None:
            return False
        if path.suffix.lower() in _BINARY_EXTS:
            return False
        xy = self._status_fn(path)
        if xy is None:
            return False
        return xy.strip() not in ("", "??")

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            repo = self._find_repo(req.path)
            if repo is None:
                return PreviewResult(kind=ContentKind.TEXT, data="Not in a git repository")

            xy = self._status_fn(req.path) if self._status_fn else "  "
            parts: list[str] = []

            if xy and xy[1] not in (" ", "?"):
                r = subprocess.run(
                    ["git", "diff", "--", str(req.path)],
                    cwd=repo, capture_output=True, text=True, timeout=5,
                )
                if r.stdout:
                    parts.append(r.stdout)

            if xy and xy[0] not in (" ", "?"):
                r = subprocess.run(
                    ["git", "diff", "--cached", "--", str(req.path)],
                    cwd=repo, capture_output=True, text=True, timeout=5,
                )
                if r.stdout:
                    if parts:
                        parts.append("\n--- Staged changes ---\n")
                    parts.append(r.stdout)

            if not parts:
                return PreviewResult(kind=ContentKind.TEXT, data="(no diff)")

            diff_text = "".join(parts)
            return PreviewResult(kind=ContentKind.HTML, data=self._to_html(diff_text))

        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return PreviewResult(kind=ContentKind.TEXT, data="(git not available)")

    @staticmethod
    def _to_html(diff_text: str) -> str:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import DiffLexer
        fmt = HtmlFormatter(nowrap=False, style="monokai")
        html = highlight(diff_text, DiffLexer(), fmt)
        css = fmt.get_style_defs(".highlight")
        return f"<style>{css}</style>{html}"

    @staticmethod
    def _find_repo(path: Path) -> Path | None:
        cur = path.parent.resolve()
        while True:
            if (cur / ".git").exists():
                return cur
            parent = cur.parent
            if parent == cur:
                return None
            cur = parent
