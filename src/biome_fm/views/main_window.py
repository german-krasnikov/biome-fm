"""Main window — dual-pane file manager shell."""

from __future__ import annotations

from biome_fm.qt import (
    QAction,
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
    back_requested = Signal()
    forward_requested = Signal()
    up_requested = Signal()
    home_requested = Signal()

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
        layout.addWidget(self._splitter, 1)

        self._cmd_line = QLineEdit()
        self._cmd_line.setPlaceholderText("Command line...")
        self._cmd_line.hide()
        layout.addWidget(self._cmd_line)

        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._build_menubar()

    def _build_menubar(self) -> None:
        mb = self.menuBar()

        fm = mb.addMenu("&File")
        fm.addAction(QAction("New &Tab\tCtrl+T", self))
        fm.addAction(QAction("Close &Tab\tCtrl+W", self))
        fm.addSeparator()
        a = QAction("&Quit", self)
        a.triggered.connect(self.close)
        fm.addAction(a)

        em = mb.addMenu("&Edit")
        for label, sig in [
            ("&Copy\tF5", self.action_bar.copy_requested),
            ("&Move\tF6", self.action_bar.move_requested),
            ("&Delete\tF8", self.action_bar.delete_requested),
            ("&Rename\tF9", self.action_bar.rename_requested),
            ("New &Folder\tF7", self.action_bar.mkdir_requested),
        ]:
            a = QAction(label, self)
            a.triggered.connect(sig.emit)
            em.addAction(a)
        em.addSeparator()
        for label in ("&Undo\tCtrl+Z", "&Redo\tCtrl+Shift+Z"):
            em.addAction(QAction(label, self))

        nm = mb.addMenu("&Navigate")
        for label, sig in [
            ("&Back\tAlt+Left", self.back_requested),
            ("&Forward\tAlt+Right", self.forward_requested),
            ("&Up\tAlt+Up", self.up_requested),
            ("&Home\tAlt+Home", self.home_requested),
        ]:
            a = QAction(label, self)
            a.triggered.connect(sig.emit)
            nm.addAction(a)

        vm = mb.addMenu("&View")
        a = QAction("Toggle &AI\tCtrl+I", self)
        a.triggered.connect(self.toggle_ai_panel)
        vm.addAction(a)
        act_cmd = QAction("&Command Line", self, checkable=True)
        act_cmd.setChecked(False)
        act_cmd.toggled.connect(self._cmd_line.setVisible)
        vm.addAction(act_cmd)

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
