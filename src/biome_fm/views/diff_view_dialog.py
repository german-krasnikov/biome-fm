"""Diff View Dialog — shows unified diff with syntax highlighting."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QWidget


class DiffViewDialog(QDialog):
    def __init__(self, diff: str, title: str = "Diff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(self._to_html(diff))
        layout.addWidget(browser)

    @staticmethod
    def _to_html(diff: str) -> str:
        if not diff:
            return "<p style='color:gray'>(files are identical)</p>"
        try:
            from pygments import highlight
            from pygments.formatters import HtmlFormatter
            from pygments.lexers import DiffLexer
            fmt = HtmlFormatter(nowrap=False, style="monokai")
            css = fmt.get_style_defs(".highlight")
            return f"<style>{css}</style>{highlight(diff, DiffLexer(), fmt)}"
        except ImportError:
            import html
            return f"<pre>{html.escape(diff)}</pre>"
