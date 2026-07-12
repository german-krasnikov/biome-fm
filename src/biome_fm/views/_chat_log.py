"""ChatLog — QTextBrowser with bubble-style messages and streaming support."""
from __future__ import annotations

import html

from biome_fm.qt import QTextBrowser

_STYLES = {
    "user": ("right", "background:#1e3a5f;color:#90caf9;border-radius:12px 12px 2px 12px"),
    "assistant": ("left", "background:#1a3a1f;color:#81c784;border-radius:12px 12px 12px 2px"),
    "error": ("left", "background:#3a1a1a;color:#ef5350;border-radius:8px"),
}


class ChatLog(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setReadOnly(True)
        self._streaming = False
        self._buf: list[str] = []

    def append_bubble(self, role: str, content: str) -> None:
        """Insert a complete message bubble."""
        align, style = _STYLES.get(role, ("left", "background:#333;color:#ccc"))
        escaped = html.escape(content).replace("\n", "<br>")
        self.append(
            f'<div style="text-align:{align};margin:4px 2px">'
            f'<span style="{style};padding:6px 10px;display:inline-block;'
            f'max-width:85%;white-space:pre-wrap;font-size:13px">'
            f"{escaped}</span></div>"
        )
        self._scroll_bottom()

    def stream_start(self) -> None:
        """Begin accumulating streaming tokens."""
        if self._streaming:
            return
        self._streaming = True
        self._buf.clear()

    def stream_token(self, token: str) -> None:
        """Accumulate token for the streaming bubble."""
        if not self._streaming:
            self.stream_start()
        self._buf.append(token)
        self._scroll_bottom()

    def stream_end(self) -> None:
        """Render the accumulated streaming tokens as a proper styled bubble."""
        self._streaming = False
        if self._buf:
            self.append_bubble("assistant", "".join(self._buf))
        self._buf.clear()

    def _scroll_bottom(self) -> None:
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
