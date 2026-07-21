"""Command Palette — Ctrl+P overlay, VSCode-style."""
from __future__ import annotations

from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.qt import (
    QFrame,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    Qt,
    QVBoxLayout,
    QWidget,
)


class _Input(QLineEdit):
    """QLineEdit that routes arrow/Escape keys to the palette."""

    def __init__(self, palette: CommandPalette) -> None:
        super().__init__()
        self._pal = palette

    def keyPressEvent(self, event: object) -> None:  # type: ignore[override]
        key = getattr(event, "key", lambda: None)()
        if key == Qt.Key.Key_Escape:
            self._pal.hide()
        elif key == Qt.Key.Key_Down:
            r = self._pal._list.currentRow()
            if r + 1 < self._pal._list.count():
                self._pal._list.setCurrentRow(r + 1)
        elif key == Qt.Key.Key_Up:
            r = self._pal._list.currentRow()
            if r > 0:
                self._pal._list.setCurrentRow(r - 1)
        else:
            super().keyPressEvent(event)  # type: ignore[arg-type]


class CommandPalette(QFrame):
    def __init__(
        self, registry: CommandRegistry, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("command-palette")
        self._registry = registry
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(580)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self._input = _Input(self)
        self._input.setPlaceholderText("Type a command...")
        self._input.textChanged.connect(self._filter)
        self._input.returnPressed.connect(self._execute)
        layout.addWidget(self._input)

        self._list = QListWidget()
        self._list.setFixedHeight(220)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.itemActivated.connect(self._run_item)
        layout.addWidget(self._list)

        self.adjustSize()

    # ── public ────────────────────────────────────────────────────────────────

    def open(self) -> None:
        self._input.clear()
        self._filter("")
        self._reposition()
        self.show()
        self.raise_()
        self._input.setFocus()

    # ── internals ─────────────────────────────────────────────────────────────

    def _reposition(self) -> None:
        p = self.parent()
        if p is None:
            return
        x = (p.width() - self.width()) // 2  # type: ignore[union-attr]
        self.move(x, 40)

    def _filter(self, query: str) -> None:
        self._list.clear()
        for entry in self._registry.search(query):
            text = f"{entry.name}  {entry.shortcut}" if entry.shortcut else entry.name
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _execute(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self._run_item(item)

    def _run_item(self, item: QListWidgetItem) -> None:
        entry: CommandEntry = item.data(Qt.ItemDataRole.UserRole)
        self._registry.record_hit(entry.name)
        self.hide()
        entry.callback()
