"""Syntax-highlighted code preview via Pygments."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_BYTES = 512 * 1024


@lru_cache(maxsize=2)
def _formatter(dark: bool):
    from pygments.formatters import HtmlFormatter
    return HtmlFormatter(
        style="monokai" if dark else "friendly",
        noclasses=True,
        prestyles="font-family: monospace; font-size: 12px;",
    )


class CodePreviewProvider:
    priority = 8

    def can_handle(self, path: Path) -> bool:
        try:
            from pygments.lexers import get_lexer_for_filename
            from pygments.lexers.special import TextLexer
            lexer = get_lexer_for_filename(path.name)
            return not isinstance(lexer, TextLexer)
        except Exception:
            return False

    def render(self, req: PreviewRequest) -> PreviewResult:
        from pygments import highlight
        from pygments.lexers import get_lexer_for_filename
        from pygments.lexers.special import TextLexer

        try:
            raw = req.path.read_bytes()
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        truncated = len(raw) > _MAX_BYTES
        text = raw[:_MAX_BYTES].decode("utf-8", errors="replace")

        try:
            lexer = get_lexer_for_filename(req.path.name, stripall=False)
            if isinstance(lexer, TextLexer):
                lexer = TextLexer()
        except Exception:
            lexer = TextLexer()

        fmt = _formatter(req.dark)
        html = highlight(text, lexer, fmt)

        if truncated:
            html += '<p style="color:gray"><em>(file truncated at 512 KB)</em></p>'

        line_count = len(text.splitlines()) or 1
        title = f"{req.path.name}  ({line_count} lines)"

        return PreviewResult(kind=ContentKind.HTML, data=html, title=title)
