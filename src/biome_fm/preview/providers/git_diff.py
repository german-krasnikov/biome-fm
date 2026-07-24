"""Git diff preview provider — shows colored diff for modified/staged files."""
from __future__ import annotations

from pathlib import Path

from biome_fm.git.run import run_git
from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.preview.providers._git_helpers import find_repo as _find_repo

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
        repo = _find_repo(req.path)
        if repo is None:
            return PreviewResult(kind=ContentKind.TEXT, data="Not in a git repository")

        xy = self._status_fn(req.path) if self._status_fn else "  "
        parts: list[str] = []

        if xy and xy[1] not in (" ", "?"):
            stdout = run_git(["diff", "--", str(req.path)], cwd=repo, timeout=5, safe=True)
            if stdout:
                parts.append(stdout)

        if xy and xy[0] not in (" ", "?"):
            stdout = run_git(["diff", "--cached", "--", str(req.path)], cwd=repo, timeout=5, safe=True)
            if stdout:
                if parts:
                    parts.append("\n--- Staged changes ---\n")
                parts.append(stdout)

        if not parts:
            return PreviewResult(kind=ContentKind.TEXT, data="(no diff)")

        diff_text = "".join(parts)
        return PreviewResult(kind=ContentKind.HTML, data=self._to_html(diff_text, req.dark))

    @staticmethod
    def _to_html(diff_text: str, dark: bool = True) -> str:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import DiffLexer
        style = "monokai" if dark else "friendly"
        fmt = HtmlFormatter(nowrap=False, style=style)
        html = highlight(diff_text, DiffLexer(), fmt)
        css = fmt.get_style_defs(".highlight")
        return f"<style>{css}</style>{html}"
