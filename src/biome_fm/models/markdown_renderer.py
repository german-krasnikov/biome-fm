"""Markdown → HTML renderer. Qt GFM parsing + Pygments code blocks."""
from __future__ import annotations

import re
from functools import lru_cache

FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
PRE_GROUP_RE = re.compile(r"(<pre[^>]*>.*?</pre>\s*)+", re.DOTALL | re.IGNORECASE)

_MAX_MD_BYTES = 100_000


@lru_cache(maxsize=2)
def _formatter(dark: bool):
    from pygments.formatters import HtmlFormatter
    return HtmlFormatter(style="monokai" if dark else "default", noclasses=True, nowrap=False)


def render(md: str, dark: bool = True) -> str:
    """Return HTML for QTextBrowser.setHtml(). Requires QApplication."""
    from pygments import highlight
    from pygments.lexers import TextLexer, get_lexer_by_name
    from PySide6.QtGui import QTextDocument

    if len(md) > _MAX_MD_BYTES:
        md = md[:_MAX_MD_BYTES] + "\n\n*(truncated)*"

    fences = list(FENCE_RE.finditer(md))
    doc = QTextDocument()
    doc.setMarkdown(
        md,
        QTextDocument.MarkdownFeature.MarkdownDialectGitHub
        | QTextDocument.MarkdownFeature.MarkdownNoHTML,
    )
    html = doc.toHtml()

    formatter = _formatter(dark)
    fence_iter = iter(fences)

    def _replace_pre(m: re.Match) -> str:
        try:
            fence = next(fence_iter)
        except StopIteration:
            return m.group(0)
        lang = fence.group(1) or "text"
        code = fence.group(2).rstrip()
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except Exception:
            lexer = TextLexer()
        return highlight(code, lexer, formatter)

    return PRE_GROUP_RE.sub(_replace_pre, html)
