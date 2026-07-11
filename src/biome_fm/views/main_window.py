"""Main window — dual-pane file manager shell."""

from __future__ import annotations

from biome_fm.qt import (
    QLineEdit,
    QMainWindow,
    QShortcut,
    QSplitter,
    QStatusBar,
    Qt,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self, left: QWidget | None = None, right: QWidget | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Biome FM")
        self.resize(1200, 700)
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
        layout.addWidget(self._splitter)

        self._cmd_line = QLineEdit()
        self._cmd_line.setPlaceholderText("Command line...")
        layout.addWidget(self._cmd_line)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _setup_shortcuts(self) -> None:
        QShortcut(Qt.Key.Key_F7, self, self._mkdir)
        QShortcut(Qt.Key.Key_Tab, self, self._switch_pane)

    def _mkdir(self) -> None:
        pass

    def _switch_pane(self) -> None:
        pass
