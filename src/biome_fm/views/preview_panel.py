"""PreviewPanel — passive sidebar panel. Implements PreviewViewProtocol."""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from biome_fm.preview.provider import ContentKind, PreviewResult


class PreviewPanel(QWidget):
    _DEFAULT_WIDTH = 350
    visibility_changed = Signal(bool)
    detach_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(0)
        self._anim: QPropertyAnimation | None = None

        self._stack = QStackedWidget()
        self._busy_label = QLabel("Loading…", alignment=Qt.AlignmentFlag.AlignCenter)
        self._img_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self._img_label.setScaledContents(False)
        self._text_view = QTextBrowser()
        self._text_view.setReadOnly(True)
        self._text_view.setOpenExternalLinks(True)
        self._dark = True

        for w in (self._busy_label, self._img_label, self._text_view):
            self._stack.addWidget(w)
        self._stack.setCurrentWidget(self._busy_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(2)
        header.addWidget(QLabel("Preview"))
        header.addStretch()
        btn_detach = QPushButton("⬒")
        btn_detach.setFixedSize(24, 24)
        btn_detach.setToolTip("Detach to window")
        btn_detach.clicked.connect(self.detach_requested)
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setToolTip("Close")
        btn_close.clicked.connect(self.close_requested)
        header.addWidget(btn_detach)
        header.addWidget(btn_close)
        layout.addLayout(header)

        layout.addWidget(self._stack)

    # ── PreviewViewProtocol ──────────────────────────────────────────────

    def show_result(self, result: PreviewResult) -> None:
        match result.kind:
            case ContentKind.IMAGE:
                px = QPixmap()
                px.loadFromData(result.data)  # type: ignore[arg-type]
                scaled = px.scaled(
                    max(self.width() - 8, 1), max(self.height() - 8, 1),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._img_label.setPixmap(scaled)
                self._stack.setCurrentWidget(self._img_label)
            case ContentKind.HTML:
                self._text_view.setHtml(result.data)  # type: ignore[arg-type]
                self._stack.setCurrentWidget(self._text_view)
            case ContentKind.TEXT:
                self._text_view.setPlainText(result.data)  # type: ignore[arg-type]
                self._stack.setCurrentWidget(self._text_view)
            case ContentKind.MARKDOWN:
                from biome_fm.models.markdown_renderer import render as _md_render
                self._text_view.setHtml(_md_render(result.data, self._dark))  # type: ignore[arg-type]
                self._stack.setCurrentWidget(self._text_view)
            case _:  # ERROR
                self._text_view.setPlainText(f"Error: {result.data}")
                self._stack.setCurrentWidget(self._text_view)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark

    def set_busy(self, busy: bool) -> None:
        if busy:
            self._stack.setCurrentWidget(self._busy_label)

    def set_visible(self, visible: bool) -> None:
        if self._anim is not None and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()
        if visible:
            self.show()
            self.setMaximumWidth(16777215)  # reset before open animation
            self._anim = self._animate(0, self._DEFAULT_WIDTH)
        else:
            self._anim = self._animate(self.width(), 0)
            self._anim.finished.connect(self.hide)

    def is_panel_visible(self) -> bool:
        return self.isVisible()

    # ── Qt events → signal ───────────────────────────────────────────────

    def showEvent(self, event: object) -> None:
        super().showEvent(event)  # type: ignore[arg-type]
        self.visibility_changed.emit(True)

    def hideEvent(self, event: object) -> None:
        super().hideEvent(event)  # type: ignore[arg-type]
        self.visibility_changed.emit(False)

    # ── Animation ────────────────────────────────────────────────────────

    def _animate(self, start: int, end: int) -> QPropertyAnimation:
        anim = QPropertyAnimation(self, b"maximumWidth", self)
        anim.setDuration(150)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        return anim
