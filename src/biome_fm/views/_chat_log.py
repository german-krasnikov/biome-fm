"""ChatLog — QTextBrowser with bubble-style messages and streaming support."""
from __future__ import annotations

import html
import re

from PySide6.QtGui import QTextBlockFormat

from biome_fm.plugins.types import _DARK_FALLBACK, ThemeTokens
from biome_fm.qt import (
    QDesktopServices,
    QTextBrowser,
    QTextCursor,
    QTimer,
    QUrl,
    Signal,
)
from biome_fm.views._linkify import _linkify_html


def _make_styles(tokens: ThemeTokens) -> dict[str, tuple[str, str]]:
    bg = tokens["surface2"]
    fg = tokens["text"]
    h = tokens["red"].lstrip("#")
    err_bg = f"rgba({int(h[:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},0.15)"
    err_fg = tokens["red"]
    return {
        "user": ("right", f"background:{bg};color:{fg};border-radius:12px 12px 2px 12px"),
        "assistant": ("left", f"background:transparent;color:{fg};border-radius:12px 12px 12px 2px"),
        "error": ("left", f"background:{err_bg};color:{err_fg};border-radius:8px"),
    }


def _make_code_css(tokens: ThemeTokens) -> str:
    s = tokens["surface"]
    b = tokens["border"]
    d = tokens["text_dim"]
    return (
        f"code, pre {{ background:{s}; border-radius:4px; font-size:0.88em; }}"
        f"pre {{ padding:8px 10px; }}"
        f"code {{ padding:2px 4px; }}"
        f"pre code {{ background:none; padding:0; }}"
        f"h1,h2,h3,h4,h5,h6 {{ margin-top:0.8em; margin-bottom:0.3em; }}"
        f"blockquote {{ border-left:3px solid {b}; margin:0.5em 0; padding:0 10px; color:{d}; }}"
        f"table {{ border-collapse:collapse; }}"
        f"th,td {{ border:1px solid {b}; padding:4px 8px; }}"
    )


_BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.DOTALL | re.IGNORECASE)


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
    shell_ops_clicked = Signal()

    def __init__(self, parent=None, *, tokens: ThemeTokens | None = None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setReadOnly(True)
        self.viewport().setAutoFillBackground(False)
        self._tokens: ThemeTokens = tokens or _DARK_FALLBACK
        self.document().setDefaultStyleSheet(_make_code_css(self._tokens))
        self.anchorClicked.connect(self._on_anchor_clicked)
        self._styles = _make_styles(self._tokens)
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
        elif url.scheme() == "shell-ops":
            self.shell_ops_clicked.emit()
        else:
            QDesktopServices.openUrl(url)

    def set_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self._styles = _make_styles(tokens)
        self.document().setDefaultStyleSheet(_make_code_css(tokens))

    def append_bubble(self, role: str, content: str) -> None:
        """Insert a complete message bubble."""
        align, style = self._styles.get(
            role,
            ("left", f"background:{self._tokens['surface2']};color:{self._tokens['text']}"),
        )
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
            f'<span style="color:{self._tokens["text_dim"]};font-style:italic;margin:4px 8px">⋯</span>'
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
            f'<span style="color:{self._tokens["text_dim"]};font-style:italic;margin:4px 8px">{dots}</span>'
        )
        self._scroll_bottom()

    def append_tool_event(self, description: str) -> None:
        self.append(
            f'<div style="color:{self._tokens["text_dim"]};font-style:italic;font-size:11px;margin:1px 8px">'
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

    def reset(self) -> None:
        """Clear all content and reset streaming state."""
        self._dot_timer.stop()
        self._streaming = False
        self._buf = []
        self._stream_block_start = 0
        self._thinking_pos = -1
        self._dot_state = 0
        super().clear()

    def _scroll_bottom(self) -> None:
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
