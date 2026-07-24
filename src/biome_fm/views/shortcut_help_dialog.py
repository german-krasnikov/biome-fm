"""Shortcut cheatsheet overlay dialog."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

SHORTCUTS: dict[str, dict[str, str]] = {
    "Navigation": {
        "Tab": "Switch pane",
        "Alt+Left": "Go back",
        "Alt+Right": "Go forward",
        "Alt+Up": "Go up",
        "Alt+Home": "Go home",
        "Alt+[": "Go back (alternate)",
        "Alt+]": "Go forward (alternate)",
        "Alt+C": "Quick CD dialog",
        "Alt+B": "Bookmarks dialog",
        "Alt+Return": "File properties",
        "Ctrl+J": "Jump to recent",
        "Ctrl+R": "Refresh",
    },
    "File Operations": {
        "F5": "Copy",
        "F6": "Move",
        "F7": "Make directory",
        "F8": "Delete",
        "F9": "Rename",
        "F2": "Open user menu",
        "Ctrl+Shift+R": "Bulk rename editor",
        "Ctrl+.": "Repeat last operation",
        "Ctrl+Alt+P": "Set permissions",
    },
    "Preview and Edit": {
        "F3": "Toggle preview",
        "F4": "Open in editor",
        "F11": "Fullscreen viewer",
    },
    "Tabs and Panes": {
        "Ctrl+T": "New tab",
        "Ctrl+W": "Close tab",
        "Ctrl+Alt+T": "Duplicate tab",
        "Ctrl+U": "Swap panes",
        "Ctrl+Shift+U": "Target = source path",
        "Ctrl+Shift+L": "Sync browsing (mirror)",
    },
    "Selection": {
        "Ctrl+G": "Select by pattern",
        "Ctrl+Shift+G": "Select by criteria",
    },
    "View": {
        "Ctrl+H": "Toggle hidden files",
        "Ctrl+Shift+.": "Toggle hidden (alternate)",
        "Ctrl+B": "Toggle sidebar",
        "Ctrl+Shift+T": "Toggle flat view",
        "Ctrl+=": "Zoom in",
        "Ctrl+-": "Zoom out",
        "Ctrl+0": "Reset zoom",
        "Ctrl+`": "Toggle terminal",
    },
    "Search": {
        "Ctrl+Shift+F": "Find files",
    },
    "Clipboard": {
        "Ctrl+Shift+C": "Copy path",
        "Alt+Shift+N": "Copy file names",
    },
    "Undo / Redo": {
        "Ctrl+Z": "Undo",
        "Ctrl+Shift+Z": "Redo",
    },
    "Bookmarks and Sessions": {
        "Ctrl+D": "Toggle bookmark",
        "Ctrl+Shift+S": "Save named session",
        "Ctrl+Shift+O": "Open saved session",
    },
    "AI and Tools": {
        "Ctrl+I": "Toggle AI panel",
        "Ctrl+Shift+N": "Natural-language file operation",
        "Ctrl+Shift+M": "Task runner",
        "Ctrl+Shift+D": "Duplicate finder",
        "Ctrl+Alt+M": "Storage treemap",
        "Ctrl+Alt+G": "Large file finder",
    },
    "Collections": {
        "Ctrl+Alt+C": "Add to collection",
        "Ctrl+Alt+V": "Show collection",
    },
    "Workspaces": {
        "Ctrl+Alt+1..5": "Load workspace 1–5",
        "Ctrl+Shift+E": "Quick open project",
    },
    "App": {
        "Ctrl+P": "Command palette",
        "Ctrl+Shift+P": "Plugin manager",
        "Ctrl+,": "Settings",
        "?/F1": "This help",
        "Alt+F4": "Quit",
    },
    "Leader chords (\\)": {
        "\\r": "Refresh",
        "\\h": "Toggle hidden",
        "\\t": "Duplicate tab",
        "\\p": "Command palette",
        "\\s": "Find files",
    },
}


class ShortcutHelpDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(480, 700)

        rows = []
        for section, entries in SHORTCUTS.items():
            rows.append(
                f"<tr><td colspan='2' style='padding:6px 8px 2px;font-weight:bold;"
                f"color:#888;text-transform:uppercase;font-size:11px'>{section}</td></tr>"
            )
            for key, desc in entries.items():
                rows.append(
                    f"<tr><td style='padding:2px 8px'><b>{key}</b></td>"
                    f"<td style='padding:2px 8px'>{desc}</td></tr>"
                )
        html = f"<table style='font-family:sans-serif;font-size:13px'>{''.join(rows)}</table>"

        self._browser = QTextBrowser()
        self._browser.setHtml(html)

        layout = QVBoxLayout(self)
        layout.addWidget(self._browser)
