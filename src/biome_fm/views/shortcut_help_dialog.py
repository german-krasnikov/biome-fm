"""Shortcut cheatsheet overlay dialog."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

SHORTCUTS: dict[str, str] = {
    "F3": "Preview file",
    "F4": "Open in editor",
    "F5": "Copy",
    "F6": "Move",
    "F7": "Make directory",
    "F8": "Delete",
    "F9": "Rename",
    "F11": "Fullscreen viewer",
    "Ctrl+T": "New tab",
    "Ctrl+W": "Close tab",
    "Ctrl+P": "Command palette",
    "Ctrl+I": "Toggle AI panel",
    "Ctrl+Shift+F": "Find files",
    "Ctrl+Z": "Undo",
    "Ctrl+Shift+Z": "Redo",
    "Ctrl+H": "Toggle hidden files",
    "Ctrl+D": "Toggle bookmark",
    "Ctrl+B": "Toggle sidebar",
    "Ctrl+J": "Jump to recent",
    "Ctrl+R": "Refresh",
    "Ctrl+Shift+C": "Copy path",
    "Ctrl+Shift+L": "Sync browsing",
    "Ctrl+G": "Select by pattern",
    "Tab": "Switch pane",
    "Alt+Left": "Go back",
    "Alt+Right": "Go forward",
    "Alt+Up": "Go up",
    "?/F1": "This help",
}


class ShortcutHelpDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(480, 500)

        rows = "".join(
            f"<tr><td style='padding:3px 8px'><b>{key}</b></td>"
            f"<td style='padding:3px 8px'>{desc}</td></tr>"
            for key, desc in SHORTCUTS.items()
        )
        html = f"<table style='font-family:sans-serif;font-size:13px'>{rows}</table>"

        self._browser = QTextBrowser()
        self._browser.setHtml(html)

        layout = QVBoxLayout(self)
        layout.addWidget(self._browser)
