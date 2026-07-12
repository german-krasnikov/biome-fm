"""Main window — dual-pane file manager shell."""

from __future__ import annotations

from biome_fm.qt import (
    QAction,
    QCompleter,
    QKeySequence,
    QLineEdit,
    QMainWindow,
    QShortcut,
    QSplitter,
    QStatusBar,
    QStringListModel,
    Qt,
    QToolBar,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views.action_bar import ActionBar


class _HistoryLineEdit(QLineEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._history: list[str] = []
        self._idx = -1

    @property
    def history(self) -> list[str]:
        return self._history

    def push(self, cmd: str) -> None:
        if cmd in self._history:
            self._history.remove(cmd)
        self._history.insert(0, cmd)
        self._history = self._history[:30]

    def keyPressEvent(self, event: object) -> None:
        if not hasattr(event, "key"):
            super().keyPressEvent(event)  # type: ignore[arg-type]
            return
        key = event.key()
        if key == Qt.Key.Key_Up and self._history:
            self._idx = min(self._idx + 1, len(self._history) - 1)
            self.setText(self._history[self._idx])
            return
        if key == Qt.Key.Key_Down:
            self._idx = max(self._idx - 1, -1)
            self.setText(self._history[self._idx] if self._idx >= 0 else "")
            return
        self._idx = -1
        super().keyPressEvent(event)  # type: ignore[arg-type]


class MainWindow(QMainWindow):
    about_to_close = Signal()
    back_requested = Signal()
    forward_requested = Signal()
    up_requested = Signal()
    home_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()
    refresh_requested = Signal()
    new_tab_requested = Signal()
    command_submitted = Signal(str)

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
        self._act_ai = QAction("AI", self, checkable=True)
        self._act_ai.setToolTip("Toggle AI panel (Ctrl+I)")
        if self._ai_panel is not None:
            self._act_ai.toggled.connect(self._ai_panel.setVisible)
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

        self._cmd_line = _HistoryLineEdit()
        self._cmd_line.setPlaceholderText("Command line...")
        self._cmd_line.returnPressed.connect(self._on_cmd)

        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setMaxVisibleItems(15)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._cmd_line.setCompleter(self._completer)

        layout.addWidget(self._cmd_line)

        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self._build_menubar()
        self._build_toolbar()

    def _on_cmd(self) -> None:
        cmd = self._cmd_line.text().strip()
        if not cmd:
            return
        self._cmd_line.push(cmd)
        self._completer_model.setStringList(self._cmd_line.history)
        self.command_submitted.emit(cmd)
        self._cmd_line.clear()

    def _build_toolbar(self) -> None:
        tb = QToolBar("Navigation", self)
        tb.setMovable(False)

        act_refresh = QAction("↺ Refresh", self)
        act_refresh.setToolTip("Refresh active pane (Ctrl+R)")
        act_refresh.triggered.connect(self.refresh_requested)
        tb.addAction(act_refresh)

        tb.addSeparator()

        act_tab = QAction("+ Tab", self)
        act_tab.setToolTip("New tab (Ctrl+T)")
        act_tab.triggered.connect(self.new_tab_requested)
        tb.addAction(act_tab)

        tb.addSeparator()
        tb.addAction(self._act_ai)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

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
        for label, sig in [
            ("&Undo\tCtrl+Z", self.undo_requested),
            ("&Redo\tCtrl+Shift+Z", self.redo_requested),
        ]:
            a = QAction(label, self)
            a.triggered.connect(sig.emit)
            em.addAction(a)

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
        a.triggered.connect(lambda: self._act_ai.toggle())
        vm.addAction(a)
        act_cmd = QAction("&Command Line", self, checkable=True)
        act_cmd.setChecked(True)
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

    def closeEvent(self, event: object) -> None:
        self.about_to_close.emit()
        super().closeEvent(event)  # type: ignore[arg-type]

    def toggle_ai_panel(self) -> None:
        if self._ai_panel is None:
            return
        self._act_ai.toggle()

    @property
    def splitter_sizes(self) -> list[int]:
        return self._splitter.sizes()
