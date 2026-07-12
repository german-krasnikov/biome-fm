"""Dark theme — macOS system colors, QSS token substitution."""
from __future__ import annotations

from string import Template

from PySide6.QtWidgets import QApplication

_TOKENS: dict[str, str] = {
    "base":     "#1c1c1e",   # macOS systemBackground
    "surface":  "#2c2c2e",   # macOS secondarySystemBackground
    "surface2": "#3a3a3c",   # macOS tertiarySystemBackground
    "border":   "#48484a",   # macOS separator
    "text":     "#f5f5f7",   # macOS label (near white)
    "text_dim": "#98989f",   # macOS secondaryLabel
    "accent":   "#0a84ff",   # macOS blue
    "accent2":  "#5e5ce6",   # macOS purple
    "red":      "#ff453a",   # macOS red
    "green":    "#32d74b",   # macOS green
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
    border-radius: 4px;
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
    selection-background-color: $accent;
    selection-color: $base;
}

QHeaderView::section {
    background-color: $surface2;
    color: $text_dim;
    border: none;
    border-bottom: 1px solid $border;
    padding: 2px 6px;
    font-size: 11px;
}

QPushButton {
    background-color: $surface2;
    color: $text;
    border: 1px solid $border;
    border-radius: 3px;
    padding: 2px 8px;
}

QPushButton:hover {
    background-color: $accent;
    color: $base;
    border-color: $accent;
}

QPushButton:pressed {
    background-color: $accent2;
}

ActionBar QPushButton {
    min-width: 0;
    padding: 1px 6px;
    font-size: 11px;
}

QToolBar {
    background-color: $surface;
    border: none;
    spacing: 2px;
    padding: 2px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 3px;
    padding: 3px 6px;
    color: $text;
}

QToolBar QToolButton:hover {
    background-color: $surface2;
}

QToolBar QToolButton:checked {
    background-color: $accent;
    color: $base;
}

QTabBar {
    background-color: $surface;
}

QTabBar::tab {
    background-color: $surface;
    color: $text_dim;
    padding: 4px 12px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: $text;
    border-bottom: 2px solid $accent;
}

QTabBar::tab:hover {
    background-color: $surface2;
}

QTabBar::close-button {
    subcontrol-position: right;
}
QTabBar::close-button:hover {
    background-color: $red;
    border-radius: 2px;
}

QMenu {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 4px 0;
}

QMenu::item {
    padding: 4px 20px;
}

QMenu::item:selected {
    background-color: $accent;
    color: $base;
}

QMenu::separator {
    height: 1px;
    background-color: $border;
    margin: 2px 0;
}

QStatusBar {
    max-height: 0;
    padding: 0;
    border: none;
    background: transparent;
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

PaneSideView[active="true"] {
    border: 1px solid $accent;
}
PaneSideView[active="false"] {
    border: 1px solid transparent;
}
""")


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(_QSS.substitute(_TOKENS))
