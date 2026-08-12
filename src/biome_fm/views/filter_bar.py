"""FilterBar — QLineEdit-based quick filter bar."""

from __future__ import annotations

from biome_fm.qt import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    Qt,
    QTimer,
    QWidget,
    Signal,
)

FILTER_PRESETS: list[tuple[str, str]] = [
    ("Images Only", "ext:png"),
    ("Large Files", "size:>10m"),
    ("Recent Files", "mod:today"),
    ("Python Files", "ext:py"),
    ("Markdown Files", "ext:md"),
    ("Documents", "ext:pdf"),
]


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
    invert_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Filter:"))
        self._preset_combo = QComboBox()
        self._preset_combo.addItem("Presets…")
        for name, _ in FILTER_PRESETS:
            self._preset_combo.addItem(name)
        self._preset_combo.setFixedWidth(110)
        self._preset_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        layout.addWidget(self._preset_combo)
        self._edit = _FilterEdit()
        self._edit.setPlaceholderText("type to filter...")
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(200)
        self._debounce.timeout.connect(self._emit_filter)
        self._edit.textChanged.connect(self._on_text_changed)
        self._edit.escape_pressed.connect(self.deactivate)
        layout.addWidget(self._edit)
        self._invert_btn = QPushButton("¬")
        self._invert_btn.setCheckable(True)
        self._invert_btn.setToolTip("Invert filter")
        self._invert_btn.setFixedWidth(28)
        self._invert_btn.toggled.connect(self.invert_toggled)
        layout.addWidget(self._invert_btn)
        self._edit.setAccessibleName("Filter text")
        self._preset_combo.setAccessibleName("Filter presets")
        self._invert_btn.setAccessibleName("Invert filter")
        self.hide()

    def _on_preset_selected(self, index: int) -> None:
        if index > 0:
            _, text = FILTER_PRESETS[index - 1]
            self._edit.setText(text)
            self._edit.setFocus()

    def _on_text_changed(self, text: str) -> None:
        self._preset_combo.blockSignals(True)
        self._preset_combo.setCurrentIndex(0)
        self._preset_combo.blockSignals(False)
        if not text:
            self._debounce.stop()
            self.filter_changed.emit("")
        else:
            self._debounce.start()

    def _emit_filter(self) -> None:
        self.filter_changed.emit(self._edit.text())

    def set_debounce_ms(self, ms: int) -> None:
        """Adjust debounce interval — use 0 in tests for immediate emit."""
        self._debounce.setInterval(ms)

    def activate(self) -> None:
        self.show()
        self._edit.setFocus()
        self._edit.selectAll()

    def set_text(self, text: str) -> None:
        """Set filter text without triggering focus/selectAll."""
        self._edit.setText(text)

    def deactivate(self) -> None:
        self._edit.clear()
        self._preset_combo.setCurrentIndex(0)
        self._invert_btn.setChecked(False)
        self.hide()
        self.closed.emit()
