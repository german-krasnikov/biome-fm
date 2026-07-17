"""ChatLog — QTextBrowser with bubble-style messages and streaming support."""
from __future__ import annotations

import html
import re

from PySide6.QtGui import QTextBlockFormat

from biome_fm.qt import (
    QDesktopServices,
    QTextBrowser,
    QTextCursor,
    QTimer,
    QUrl,
    Signal,
)
from biome_fm.views._linkify import _linkify_html

def _make_styles(dark: bool) -> dict[str, tuple[str, str]]:
    if dark:
        return {
            "user": ("right", "background:#1a2840;color:#e0e0e0;border-radius:12px 12px 2px 12px"),
            "assistant": ("left", "background:transparent;color:#e0e0e0;border-radius:12px 12px 12px 2px"),
            "error": ("left", "background:#2a1a1a;color:#ef9a9a;border-radius:8px"),
        }
    return {
        "user": ("right", "background:#cce4ff;color:#1a2840;border-radius:12px 12px 2px 12px"),
        "assistant": ("left", "background:transparent;color:#1a2840;border-radius:12px 12px 12px 2px"),
        "error": ("left", "background:#ffd6d6;color:#8b0000;border-radius:8px"),
    }

_BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.DOTALL | re.IGNORECASE)

_CODE_CSS = """
code, pre { background:#2d2d2d; border-radius:4px; font-size:0.88em; }
pre { padding:8px 10px; }
code { padding:2px 4px; }
pre code { background:none; padding:0; }
h1,h2,h3,h4,h5,h6 { margin-top:0.8em; margin-bottom:0.3em; }
blockquote { border-left:3px solid #555; margin:0.5em 0; padding:0 10px; color:#aaa; }
table { border-collapse:collapse; }
th,td { border:1px solid #444; padding:4px 8px; }
"""


def _md_fragment(content: str) -> str:
    """Render markdown to HTML body fragment; fallback to escaped plain text."""
    try:
        from biome_fm.preview import markdown_renderer  # lazy — needs QApplication
        full_html = markdown_renderer.render(content, dark=True)
        m = _BODY_RE.search(full_html)
        return m.group(1) if m else html.escape(content)
    except Exception:
        return html.escape(content)


class ChatLog(QTextBrowser):
    _DOTS = ("⋯", "⋯.", "⋯..", "⋯...")

    path_link_clicked = Signal(str)

    def __init__(self, parent=None, *, dark: bool = True):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setReadOnly(True)
        self.viewport().setAutoFillBackground(False)
        self.document().setDefaultStyleSheet(_CODE_CSS)
        self.anchorClicked.connect(self._on_anchor_clicked)
        self._styles = _make_styles(dark)
        self._streaming = False
        self._buf: list[str] = []
        self._stream_block_start: int = 0
        self._thinking_pos: int = -1
        self._dot_state: int = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(450)
        self._dot_timer.timeout.connect(self._tick_dots)

    def _on_anchor_clicked(self, url: QUrl) -> None:
        if url.scheme() == "biome":
            self.path_link_clicked.emit(url.toString().removeprefix("biome:"))
        else:
            QDesktopServices.openUrl(url)

    def set_dark(self, dark: bool) -> None:
        self._styles = _make_styles(dark)

    def append_bubble(self, role: str, content: str) -> None:
        """Insert a complete message bubble."""
        align, style = self._styles.get(role, ("left", "background:#333;color:#ccc"))
        cursor = QTextCursor(self.document())
        cursor.movePosition(cursor.MoveOperation.End)
        if cursor.position() > 0 and cursor.block().text():
            self._insert_clean_block(cursor)
        if role == "assistant":
            body = _linkify_html(_md_fragment(content))
            cursor.insertHtml(
                f'<div style="text-align:{align};margin:4px 2px">'
                f'<div style="{style};padding:6px 10px;display:inline-block;'
                f'max-width:85%;font-size:13px">'
                f"{body}</div></div>"
            )
        else:
            escaped = html.escape(content).replace("\n", "<br>")
            cursor.insertHtml(
                f'<div style="text-align:{align};margin:4px 2px">'
                f'<span style="{style};padding:6px 10px;display:inline-block;'
                f'max-width:85%;white-space:pre-wrap;font-size:13px">'
                f"{escaped}</span></div>"
            )
        self._scroll_bottom()

    @staticmethod
    def _insert_clean_block(cursor: QTextCursor) -> None:
        fmt = QTextBlockFormat()
        cursor.insertBlock(fmt)

    def show_thinking(self) -> None:
        if self._thinking_pos >= 0:
            return
        cursor = QTextCursor(self.document())
        cursor.movePosition(cursor.MoveOperation.End)
        self._insert_clean_block(cursor)
        self._thinking_pos = cursor.position()
        cursor.insertHtml(
            '<span style="color:#888;font-style:italic;margin:4px 8px">⋯</span>'
        )
        self._dot_state = 0
        self._dot_timer.start()
        self._scroll_bottom()

    def hide_thinking(self) -> None:
        self._dot_timer.stop()
        if self._thinking_pos < 0:
            return
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._thinking_pos)
        cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self._thinking_pos = -1

    def _tick_dots(self) -> None:
        if self._thinking_pos < 0:
            return
        self._dot_state = (self._dot_state + 1) % len(self._DOTS)
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._thinking_pos)
        cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
        dots = self._DOTS[self._dot_state]
        cursor.insertHtml(
            f'<span style="color:#888;font-style:italic;margin:4px 8px">{dots}</span>'
        )
        self._scroll_bottom()

    def append_tool_event(self, description: str) -> None:
        self.append(
            f'<div style="color:#888;font-style:italic;font-size:11px;margin:1px 8px">'
            f"&#9881; {html.escape(description)}</div>"
        )
        self._scroll_bottom()

    def stream_start(self) -> None:
        """Begin accumulating streaming tokens."""
        self.hide_thinking()
        if self._streaming:
            return
        self._streaming = True
        self._buf.clear()
        cursor = QTextCursor(self.document())
        cursor.movePosition(cursor.MoveOperation.End)
        self._insert_clean_block(cursor)
        self._stream_block_start = cursor.position()

    def stream_token(self, token: str) -> None:
        """Append token at end — O(1) per token, no full-buffer rewrite."""
        if not self._streaming:
            self.stream_start()
        self._buf.append(token)
        cursor = QTextCursor(self.document())
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self._scroll_bottom()

    def stream_end(self) -> None:
        """Replace raw streaming text with a styled bubble."""
        self._streaming = False
        if self._buf:
            cursor = QTextCursor(self.document())
            cursor.setPosition(self._stream_block_start)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self.append_bubble("assistant", "".join(self._buf))
        self._buf.clear()
        self._stream_block_start = 0

    def stream_discard(self) -> None:
        """Discard any in-progress stream without rendering a bubble."""
        self.hide_thinking()
        if not self._streaming:
            return
        self._streaming = False
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._stream_block_start)
        cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self._buf.clear()
        self._stream_block_start = 0

    def _scroll_bottom(self) -> None:
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
