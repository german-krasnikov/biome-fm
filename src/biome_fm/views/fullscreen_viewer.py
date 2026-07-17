"""Fullscreen preview viewer with arrow-key file navigation."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from biome_fm.models.file_item import FileItem
from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from PySide6.QtGui import QPixmap

from biome_fm.qt import (
    QDialog, QLabel, QTextBrowser, QVBoxLayout, QWidget, Qt,
)


class FullscreenViewer(QDialog):
    """Maximized preview dialog with Left/Right arrow key navigation."""

    def __init__(
        self,
        items: list[FileItem],
        idx: int,
        render_fn: Callable[[PreviewRequest], PreviewResult],
        dark: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        # Filter to files only (no dirs, no "..")
        self._items = [i for i in items if not i.is_dir and i.name != ".."]
        selected = items[idx] if idx < len(items) else None
        self._idx = self._items.index(selected) if selected in self._items else 0
        self._render_fn = render_fn
        self._dark = dark

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text = QTextBrowser()
        self._text.setOpenExternalLinks(True)
        layout.addWidget(self._text)

        self._image = QLabel()
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setVisible(False)
        layout.addWidget(self._image)

        self._show_current()

    # ── public ────────────────────────────────────────────────────────────────

    def _go(self, delta: int) -> None:
        if not self._items:
            return
        self._idx = (self._idx + delta) % len(self._items)
        self._show_current()

    # ── private ───────────────────────────────────────────────────────────────

    def _show_current(self) -> None:
        if not self._items:
            self._text.setPlainText("No files to preview")
            return
        item = self._items[self._idx]
        self.setWindowTitle(f"{item.name} ({self._idx + 1}/{len(self._items)})")
        result = self._render_fn(PreviewRequest(path=item.path, dark=self._dark))
        self._text.setVisible(False)
        self._image.setVisible(False)
        if result.kind == ContentKind.IMAGE:
            px = QPixmap()
            if isinstance(result.data, bytes):
                px.loadFromData(result.data)
            else:
                px.load(str(result.data))
            self._image.setPixmap(
                px.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
            )
            self._image.setVisible(True)
        elif result.kind == ContentKind.HTML:
            self._text.setHtml(str(result.data))
            self._text.setVisible(True)
        else:
            self._text.setPlainText(str(result.data))
            self._text.setVisible(True)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self.close()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_Space):
            self._go(1)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            self._go(-1)
        else:
            super().keyPressEvent(event)
