"""Markdown → HTML renderer. Qt GFM parsing + Pygments code blocks."""
from __future__ import annotations

import re
from functools import lru_cache

FENCE_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
PRE_RE = re.compile(r"<pre[^>]*>.*?</pre>", re.DOTALL | re.IGNORECASE)

_MAX_MD_BYTES = 100_000


@lru_cache(maxsize=2)
def _formatter(dark: bool):
    from pygments.formatters import HtmlFormatter
    return HtmlFormatter(style="monokai" if dark else "default", noclasses=True, nowrap=False)


def _css(dark: bool) -> str:
    bg, text, code_bg, border, muted = (
        ("#1e1e1e", "#d4d4d4", "#2d2d2d", "#444", "#888")
        if dark else
        ("#ffffff", "#111111", "#f0f0f0", "#ccc", "#666")
    )
    return f"""
body {{ background:{bg}; color:{text}; font-family:system-ui,sans-serif;
        font-size:13px; line-height:1.65; padding:12px 16px; margin:0; }}
h1,h2,h3,h4,h5,h6 {{ margin:1.2em 0 0.4em; line-height:1.3; }}
h1 {{ font-size:1.8em; }} h2 {{ font-size:1.45em; }} h3 {{ font-size:1.2em; }}
pre {{ background:{code_bg}; padding:10px 12px; border-radius:5px;
       overflow-x:auto; font-size:0.85em; margin:0.8em 0; }}
code {{ background:{code_bg}; padding:2px 5px; border-radius:3px; font-size:0.88em; }}
pre code {{ background:none; padding:0; }}
table {{ border-collapse:collapse; width:100%; margin:0.8em 0; }}
th,td {{ border:1px solid {border}; padding:5px 10px; text-align:left; }}
th {{ background:{code_bg}; }}
blockquote {{ border-left:3px solid {border}; margin:0.5em 0; padding:0 12px; color:{muted}; }}
a {{ color:#4ea6dc; }} a:visited {{ color:#9b7fcc; }}
"""


def _inject_css(html: str, dark: bool) -> str:
    css = _css(dark)
    if "</style></head>" in html:
        return html.replace("</style></head>", f"\n{css}</style></head>", 1)
    return f"<html><head><style>{css}</style></head><body>{html}</body></html>"


def render(md: str, dark: bool = True) -> str:
    """Return HTML for QTextBrowser.setHtml(). Requires QApplication."""
    from pygments import highlight
    from pygments.lexers import TextLexer, get_lexer_by_name
    from PySide6.QtGui import QTextDocument

    if len(md) > _MAX_MD_BYTES:
        md = md[:_MAX_MD_BYTES] + "\n\n*(truncated)*"

    fences = list(FENCE_RE.finditer(md))
    doc = QTextDocument()
    doc.setMarkdown(md, QTextDocument.MarkdownFeature.MarkdownDialectGitHub)
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

    html = PRE_RE.sub(_replace_pre, html)
    return _inject_css(html, dark)
