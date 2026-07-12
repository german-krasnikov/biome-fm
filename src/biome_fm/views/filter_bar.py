"""FilterBar — QLineEdit-based quick filter bar."""

from __future__ import annotations

from biome_fm.qt import QHBoxLayout, QLabel, QLineEdit, Qt, QWidget, Signal


class _FilterEdit(QLineEdit):
    escape_pressed = Signal()

    def keyPressEvent(self, event: object) -> None:
        if hasattr(event, "key") and event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            return
        super().keyPressEvent(event)  # type: ignore[arg-type]


class FilterBar(QWidget):
    filter_changed = Signal(str)
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Filter:"))
        self._edit = _FilterEdit()
        self._edit.setPlaceholderText("type to filter...")
        self._edit.textChanged.connect(self.filter_changed)
        self._edit.escape_pressed.connect(self.deactivate)
        layout.addWidget(self._edit)
        self.hide()

    def activate(self) -> None:
        self.show()
        self._edit.setFocus()
        self._edit.selectAll()

    def deactivate(self) -> None:
        self._edit.clear()
        self.hide()
        self.closed.emit()
