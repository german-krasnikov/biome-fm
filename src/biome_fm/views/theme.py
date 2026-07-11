"""Dark theme — Tokyo Night palette, QSS token substitution."""
from __future__ import annotations

from string import Template

from PySide6.QtWidgets import QApplication

_TOKENS: dict[str, str] = {
    "base":     "#1A1B26",
    "surface":  "#24283B",
    "surface2": "#2E3149",
    "border":   "#414868",
    "text":     "#C0CAF5",
    "text_dim": "#565F89",
    "accent":   "#7AA2F7",
    "accent2":  "#BB9AF7",
    "red":      "#F7768E",
    "green":    "#9ECE6A",
}

_QSS = Template("""
QWidget {
    background-color: $base;
    color: $text;
    font-size: 13px;
}

QMainWindow, QFrame {
    background-color: $base;
}

QSplitter::handle {
    background-color: $border;
    width: 1px;
}

QLineEdit {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 3px;
    padding: 2px 6px;
    selection-background-color: $accent;
    selection-color: $base;
}

QLineEdit:focus {
    border-color: $accent;
}

QTableView {
    background-color: $surface;
    alternate-background-color: $surface2;
    color: $text;
    border: none;
    gridline-color: $border;
    selection-background-color: $accent;
    selection-color: $base;
}

QHeaderView::section {
    background-color: $surface2;
    color: $text_dim;
    border: none;
    border-bottom: 1px solid $border;
    padding: 4px 6px;
}

QPushButton {
    background-color: $surface2;
    color: $text;
    border: 1px solid $border;
    border-radius: 3px;
    padding: 3px 10px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: $accent;
    color: $base;
    border-color: $accent;
}

QPushButton:pressed {
    background-color: $accent2;
}

QStatusBar {
    background-color: $surface;
    color: $text_dim;
}

QLabel {
    color: $text_dim;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: $surface;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: $border;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QListWidget {
    background-color: $surface;
    color: $text;
    border: none;
    outline: none;
}

QListWidget::item:selected {
    background-color: $accent;
    color: $base;
}

QListWidget::item:hover {
    background-color: $surface2;
}

QFrame#command-palette {
    background-color: $surface;
    border: 1px solid $accent;
    border-radius: 6px;
}
""")


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(_QSS.substitute(_TOKENS))
