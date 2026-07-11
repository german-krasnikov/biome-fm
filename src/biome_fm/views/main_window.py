"""Main window — dual-pane file manager shell."""

from __future__ import annotations

from biome_fm.qt import (
    QKeySequence,
    QLineEdit,
    QMainWindow,
    QShortcut,
    QSplitter,
    QStatusBar,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views.action_bar import ActionBar


class MainWindow(QMainWindow):
    about_to_close = Signal()

    def __init__(
        self,
        left: QWidget | None = None,
        right: QWidget | None = None,
        ai_panel: QWidget | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Biome FM")
        self.resize(1200, 700)
        self._ai_panel = ai_panel
        self._setup_ui(left, right)
        self._setup_shortcuts()

    def _setup_ui(self, left: QWidget | None, right: QWidget | None) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        if left is not None:
            self._splitter.addWidget(left)
        if right is not None:
            self._splitter.addWidget(right)
        if self._ai_panel is not None:
            self._splitter.addWidget(self._ai_panel)
            self._ai_panel.hide()
        layout.addWidget(self._splitter)

        self._cmd_line = QLineEdit()
        self._cmd_line.setPlaceholderText("Command line...")
        layout.addWidget(self._cmd_line)

        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _setup_shortcuts(self) -> None:
        for key, signal in [
            ("F5", self.action_bar.copy_requested),
            ("F6", self.action_bar.move_requested),
            ("F7", self.action_bar.mkdir_requested),
            ("F8", self.action_bar.delete_requested),
            ("F9", self.action_bar.rename_requested),
        ]:
            QShortcut(QKeySequence(key), self).activated.connect(signal)
        self.tab_shortcut = QShortcut(Qt.Key.Key_Tab, self)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.about_to_close.emit()
        super().closeEvent(event)

    def toggle_ai_panel(self) -> None:
        if self._ai_panel is None:
            return
        self._ai_panel.setVisible(not self._ai_panel.isVisible())

    @property
    def splitter_sizes(self) -> list[int]:
        return self._splitter.sizes()
