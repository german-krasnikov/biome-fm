"""ZoomableImageWidget — scroll area with zoom/pan/rotate for image preview."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy, QWidget


class ZoomableImageWidget(QScrollArea):
    _ZOOM_FACTOR = 1.25

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scale = 1.0
        self._angle = 0
        self._px = QPixmap()

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setWidget(self._label)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_pixmap(self, px: QPixmap) -> None:
        self._px = px
        self._scale = 1.0
        self._angle = 0
        self._update()

    def _zoom_in(self) -> None:
        self._scale *= self._ZOOM_FACTOR
        self._update()

    def _zoom_out(self) -> None:
        self._scale /= self._ZOOM_FACTOR
        self._update()

    def _reset(self) -> None:
        self._scale = 1.0
        self._angle = 0
        self._update()

    def fit_to_window(self) -> None:
        if self._px.isNull():
            return
        vp = self.viewport().size()
        if not vp.width() or not vp.height():
            return
        w, h = (self._px.height(), self._px.width()) if self._angle % 180 else (self._px.width(), self._px.height())
        self._scale = min(vp.width() / w, vp.height() / h)
        self._update()

    def actual_size(self) -> None:
        self._scale = 1.0
        self._update()

    def _update(self) -> None:
        if self._px.isNull():
            return
        t = QTransform().rotate(self._angle).scale(self._scale, self._scale)
        self._label.setPixmap(
            self._px.transformed(t, Qt.TransformationMode.SmoothTransformation)
        )
        self._label.adjustSize()

    # ── Qt events ────────────────────────────────────────────────────────────

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self._reset()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_R:
            self._angle = (self._angle + 90) % 360
            self._update()
        elif event.key() == Qt.Key.Key_0:
            self.fit_to_window()
        elif event.key() == Qt.Key.Key_1:
            self.actual_size()
        else:
            super().keyPressEvent(event)
