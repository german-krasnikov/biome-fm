"""Diff View Dialog — side-by-side diff with color highlighting."""
from __future__ import annotations

import html as _html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QSplitter, QTextBrowser, QVBoxLayout, QWidget


class DiffViewDialog(QDialog):
    def __init__(self, diff: str, title: str = "Diff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1000, 600)
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_browser = QTextBrowser()
        self.right_browser = QTextBrowser()
        splitter.addWidget(self.left_browser)
        splitter.addWidget(self.right_browser)
        layout.addWidget(splitter)

        if not diff:
            msg = "<p style='color:gray'>(files are identical)</p>"
            self.left_browser.setHtml(msg)
            self.right_browser.setHtml(msg)
            return

        left_lines, right_lines = self._split_diff(diff)
        self.left_browser.setHtml(self._render_side(left_lines))
        self.right_browser.setHtml(self._render_side(right_lines))

    @staticmethod
    def _split_diff(diff: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        """Parse unified diff → (left_lines, right_lines) each as (kind, text)."""
        left: list[tuple[str, str]] = []
        right: list[tuple[str, str]] = []
        for line in diff.splitlines():
            if line.startswith(("---", "+++", "@@", "\\")):
                continue
            if line.startswith("-"):
                left.append(("removed", line[1:]))
                right.append(("placeholder", ""))
            elif line.startswith("+"):
                left.append(("placeholder", ""))
                right.append(("added", line[1:]))
            else:
                text = line[1:] if line.startswith(" ") else line
                left.append(("context", text))
                right.append(("context", text))
        return left, right

    @staticmethod
    def _render_side(lines: list[tuple[str, str]]) -> str:
        parts: list[str] = []
        for kind, text in lines:
            esc = _html.escape(text) if text else "&nbsp;"
            if kind == "removed":
                parts.append(f"<p style='margin:0;font-family:monospace;background-color:#3c1010;color:#ff6b6b'>{esc}</p>")
            elif kind == "added":
                parts.append(f"<p style='margin:0;font-family:monospace;background-color:#0d3c0d;color:#6bff6b'>{esc}</p>")
            elif kind == "placeholder":
                parts.append("<p style='margin:0;font-family:monospace;background-color:#2a2a2a'>&nbsp;</p>")
            else:
                parts.append(f"<p style='margin:0;font-family:monospace'>{esc}</p>")
        return "".join(parts)
