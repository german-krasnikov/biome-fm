"""TreemapPanel — QPainter-based storage visualization widget (F330)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QPushButton, QToolTip, QVBoxLayout, QWidget

from biome_fm.presenters.treemap_presenter import TreemapNode, TreemapPresenter, squarify


class TreemapPanel(QWidget):
    path_clicked = Signal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Storage Treemap")
        self.resize(800, 600)
        self.setMouseTracking(True)

        self._status = QLabel("Select a directory to scan.", self)
        self._close_btn = QPushButton("Close", self)
        self._close_btn.clicked.connect(self.close)

        top = QWidget(self)
        from PySide6.QtWidgets import QHBoxLayout
        hbox = QHBoxLayout(top)
        hbox.setContentsMargins(4, 4, 4, 4)
        hbox.addWidget(self._status)
        hbox.addStretch()
        hbox.addWidget(self._close_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(top)

        self._nodes: list[TreemapNode] = []
        self._rects: list[tuple[TreemapNode, tuple[float, float, float, float]]] = []

        self._presenter = TreemapPresenter(self)

        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(100)
        self._drain_timer.timeout.connect(self._presenter.drain)
        self._drain_timer.start()

    def scan(self, path: Path) -> None:
        self._nodes = []
        self._rects = []
        self._status.setText(f"Scanning {path}…")
        self.update()
        self._presenter.scan(path)

    # --- TreemapViewProtocol ---

    def set_nodes(self, nodes: list[TreemapNode]) -> None:
        self._nodes = nodes
        self._recompute_rects()
        self._status.setText(f"{len(nodes)} file types found.")
        self.update()

    # --- Qt events ---

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._recompute_rects()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for node, (x, y, w, h) in self._rects:
            if w < 2 or h < 2:
                continue
            painter.fillRect(QRectF(x, y, w, h), QColor(node.color))
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawRect(QRectF(x, y, w, h))
            if w > 40 and h > 14:
                painter.setPen(QColor("#ffffff"))
                label = Path(node.path).suffix or str(node.path.name)
                painter.drawText(QRectF(x + 2, y + 2, w - 4, h - 4), label)

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        for node, (x, y, w, h) in self._rects:
            if x <= pos.x() < x + w and y <= pos.y() < y + h:
                size_str = _fmt(node.size)
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"{node.path}\n{size_str}",
                    self,
                )
                return
        QToolTip.hideText()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        for node, (x, y, w, h) in self._rects:
            if x <= pos.x() < x + w and y <= pos.y() < y + h:
                self.path_clicked.emit(node.path)
                return

    # --- private ---

    def _recompute_rects(self) -> None:
        if not self._nodes:
            self._rects = []
            return
        canvas_y = 40  # leave room for top bar
        w = float(self.width())
        h = float(self.height() - canvas_y)
        self._rects = squarify(self._nodes, 0.0, float(canvas_y), w, h)


def _fmt(n: int) -> str:
    s = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if s < 1024:
            return f"{s:.1f} {unit}"
        s /= 1024
    return f"{s:.1f} TB"
