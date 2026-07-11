"""Main window — dual-pane file manager shell."""

from biome_fm.qt import QMainWindow, QSplitter, Qt, QShortcut, QStatusBar, QLineEdit, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Biome FM")
        self.resize(1200, 700)
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
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
