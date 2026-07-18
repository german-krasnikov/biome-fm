"""Main window — dual-pane file manager shell."""

from __future__ import annotations

from biome_fm.qt import (
    QAction,
    QCompleter,
    QKeySequence,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
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
from biome_fm.utils.path_completion import path_completions
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
        if key == Qt.Key.Key_Tab:
            matches = path_completions(self.text())
            if matches:
                c = self.completer()
                if c is not None:
                    c.model().setStringList(matches)
                    c.complete()
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
    close_tab_requested = Signal()
    command_submitted = Signal(str)
    preview_toggle_requested = Signal()
    ai_toggle_requested = Signal()
    settings_requested = Signal()
    detach_preview_requested = Signal()
    detach_ai_requested = Signal()
    search_requested = Signal()
    terminal_requested = Signal()
    tag_filter_requested = Signal()
    transfer_queue_requested = Signal()
    flat_view_requested = Signal()
    workspaces_requested = Signal()
    sidebar_toggle_requested = Signal()
    find_duplicates_requested = Signal()
    temp_panel_requested = Signal()
    highlight_rules_requested = Signal()
    sync_dirs_requested = Signal()
    nl_op_requested = Signal()
    panelize_requested = Signal()
    cloud_profiles_requested = Signal()

    def __init__(
        self,
        left: QWidget | None = None,
        right: QWidget | None = None,
        ai_panel: QWidget | None = None,
        preview_panel: QWidget | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Biome FM")
        self.resize(1200, 700)
        self._ai_panel = ai_panel
        self._preview_panel = preview_panel
        self._close_guard = None  # Callable[[], bool] | None — set by app.py
        self._act_ai = QAction("AI", self, checkable=True)
        self._act_ai.setToolTip("Toggle AI panel (Ctrl+I)")
        self._act_ai.triggered.connect(lambda _: self.ai_toggle_requested.emit())
        self._act_preview = QAction("Preview", self, checkable=True)
        self._act_preview.setToolTip("Toggle Preview panel (Space / F3)")
        self._act_preview.triggered.connect(lambda _: self.preview_toggle_requested.emit())
        self._setup_ui(left, right)
        self._setup_shortcuts()
        self._setup_accessibility()

    def _setup_accessibility(self) -> None:
        self._cmd_line.setAccessibleName("Command line")
        self.action_bar.setAccessibleName("Action bar")

    def _setup_ui(self, left: QWidget | None, right: QWidget | None) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        if left is not None:
            self._splitter.addWidget(left)
        if right is not None:
            self._splitter.addWidget(right)
        if self._preview_panel is not None:
            self._splitter.addWidget(self._preview_panel)
            self._preview_panel.hide()
        if self._ai_panel is not None:
            self._splitter.addWidget(self._ai_panel)
            self._ai_panel.hide()
        for i in range(self._splitter.count()):
            self._splitter.setStretchFactor(i, 1 if i < 2 else 0)
            if i < 2:
                self._splitter.setCollapsible(i, False)
        handle = self._splitter.handle(1)
        if handle is not None:
            handle.installEventFilter(self)
        layout.addWidget(self._splitter, 1)

        self._cmd_line = _HistoryLineEdit()
        self._cmd_line.setPlaceholderText("Command line...")
        self._cmd_line.returnPressed.connect(self._on_cmd)

        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setMaxVisibleItems(15)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._cmd_line.setCompleter(self._completer)

        self.action_bar = ActionBar()
        layout.addWidget(self.action_bar)

        layout.addWidget(self._cmd_line)

        self.setCentralWidget(central)
        sb = QStatusBar()
        self._git_label = QLabel()
        self._ops_label = QLabel()
        self._remote_status_label = QLabel()
        self._remote_status_label.hide()
        sb.addPermanentWidget(self._remote_status_label)
        sb.addPermanentWidget(self._git_label)
        sb.addPermanentWidget(self._ops_label)
        self.setStatusBar(sb)
        self._build_menubar()
        self._build_drag_toolbar()
        self._subscribe_remote_events()

    def _build_drag_toolbar(self) -> None:
        import sys
        if sys.platform != "darwin":
            return
        tb = QToolBar(self)
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setFixedHeight(0)
        tb.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        self.setUnifiedTitleAndToolBarOnMac(True)

    def _on_cmd(self) -> None:
        cmd = self._cmd_line.text().strip()
        if not cmd:
            return
        self._cmd_line.push(cmd)
        self._completer_model.setStringList(self._cmd_line.history)
        self.command_submitted.emit(cmd)
        self._cmd_line.clear()

    def _build_menubar(self) -> None:
        mb = self.menuBar()

        fm = mb.addMenu("&File")
        a = QAction("New &Tab\tCtrl+T", self)
        a.triggered.connect(lambda _: self.new_tab_requested.emit())
        fm.addAction(a)
        a = QAction("Close &Tab\tCtrl+W", self)
        a.triggered.connect(lambda _: self.close_tab_requested.emit())
        fm.addAction(a)
        fm.addSeparator()
        a = QAction("&Settings\tCtrl+,", self)
        a.setMenuRole(QAction.MenuRole.NoRole)
        a.triggered.connect(lambda _: self.settings_requested.emit())
        fm.addAction(a)
        fm.addSeparator()
        a = QAction("&Quit", self)
        a.setMenuRole(QAction.MenuRole.NoRole)
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
        self._act_undo = QAction("&Undo\tCtrl+Z", self)
        self._act_undo.triggered.connect(self.undo_requested.emit)
        em.addAction(self._act_undo)
        self._act_redo = QAction("&Redo\tCtrl+Shift+Z", self)
        self._act_redo.triggered.connect(self.redo_requested.emit)
        em.addAction(self._act_redo)
        em.addSeparator()
        a = QAction("&Find Files\tCtrl+Shift+F", self)
        a.triggered.connect(lambda _: self.search_requested.emit())
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
        a = QAction("&Sidebar\tCtrl+B", self)
        a.triggered.connect(lambda _: self.sidebar_toggle_requested.emit())
        vm.addAction(a)
        vm.addSeparator()
        a = QAction("&Refresh\tCtrl+R", self)
        a.triggered.connect(lambda _: self.refresh_requested.emit())
        vm.addAction(a)
        vm.addSeparator()
        vm.addAction(self._act_preview)
        vm.addAction(self._act_ai)
        a = QAction("&Terminal\tCtrl+`", self)
        a.triggered.connect(lambda _: self.terminal_requested.emit())
        vm.addAction(a)
        act_cmd = QAction("&Command Line", self, checkable=True)
        act_cmd.setChecked(True)
        act_cmd.toggled.connect(self._cmd_line.setVisible)
        vm.addAction(act_cmd)
        vm.addSeparator()
        a = QAction("Detach Preview", self)
        a.triggered.connect(lambda _: self.detach_preview_requested.emit())
        vm.addAction(a)
        a = QAction("Detach AI", self)
        a.triggered.connect(lambda _: self.detach_ai_requested.emit())
        vm.addAction(a)
        vm.addSeparator()
        a = QAction("&Transfer Queue", self)
        a.triggered.connect(lambda _: self.transfer_queue_requested.emit())
        vm.addAction(a)
        vm.addSeparator()
        a = QAction("Flat &View\tCtrl+Shift+T", self)
        a.triggered.connect(lambda _: self.flat_view_requested.emit())
        vm.addAction(a)
        vm.addSeparator()
        a = QAction("&Workspaces...", self)
        a.triggered.connect(lambda _: self.workspaces_requested.emit())
        vm.addAction(a)

        tm = mb.addMenu("&Tools")
        a = QAction("&Synchronize Directories...\tCtrl+Shift+Y", self)
        a.triggered.connect(lambda _: self.sync_dirs_requested.emit())
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("Find &Duplicates...\tCtrl+Shift+D", self)
        a.triggered.connect(lambda _: self.find_duplicates_requested.emit())
        tm.addAction(a)
        a = QAction("&Temp Files...", self)
        a.triggered.connect(lambda _: self.temp_panel_requested.emit())
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("&Highlight Rules...", self)
        a.triggered.connect(lambda _: self.highlight_rules_requested.emit())
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("&Natural Language Op...\tCtrl+Shift+N", self)
        a.triggered.connect(lambda _: self.nl_op_requested.emit())
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("&Panelize...", self)
        a.triggered.connect(lambda _: self.panelize_requested.emit())
        tm.addAction(a)
        tm.addSeparator()
        a = QAction("Cloud &Profiles...", self)
        a.triggered.connect(lambda _: self.cloud_profiles_requested.emit())
        tm.addAction(a)

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

    def update_undo_redo_labels(self, undo_desc: str | None, redo_desc: str | None) -> None:
        self._act_undo.setText(f"&Undo {undo_desc}\tCtrl+Z" if undo_desc else "&Undo\tCtrl+Z")
        self._act_redo.setText(f"&Redo {redo_desc}\tCtrl+Shift+Z" if redo_desc else "&Redo\tCtrl+Shift+Z")

    def _show_ratio_menu(self, global_pos: object) -> None:
        menu = QMenu(self)
        for label, ratio in [("25 / 75", 0.25), ("50 / 50", 0.5), ("75 / 25", 0.75)]:
            action = menu.addAction(label)
            action.triggered.connect(lambda checked=False, r=ratio: self._set_pane_ratio(r))
        menu.exec(global_pos)  # type: ignore[arg-type]

    def _set_pane_ratio(self, left_ratio: float) -> None:
        sizes = self._splitter.sizes()
        pane_total = sizes[0] + sizes[1]
        if pane_total > 0:
            sizes[0] = int(pane_total * left_ratio)
            sizes[1] = pane_total - sizes[0]
            self._splitter.setSizes(sizes)

    def eventFilter(self, obj: object, event: object) -> bool:
        from PySide6.QtCore import QEvent
        if obj is self._splitter.handle(1) and hasattr(event, "type"):
            etype = event.type()  # type: ignore[union-attr]
            if etype == QEvent.Type.ContextMenu:
                self._show_ratio_menu(event.globalPos())  # type: ignore[union-attr]
                return True
            if (
                hasattr(event, "button")
                and etype == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.MiddleButton  # type: ignore[union-attr]
            ):
                self._show_ratio_menu(event.globalPos())  # type: ignore[union-attr]
                return True
        return super().eventFilter(obj, event)  # type: ignore[arg-type]

    def closeEvent(self, event: object) -> None:
        if self._close_guard is not None and not self._close_guard():
            if hasattr(event, "ignore"):
                event.ignore()  # type: ignore[union-attr]
            return
        self.about_to_close.emit()
        super().closeEvent(event)  # type: ignore[arg-type]

    @property
    def splitter(self) -> QSplitter:
        return self._splitter

    @property
    def splitter_sizes(self) -> list[int]:
        return self._splitter.sizes()

    def update_git_branch(self, branch: str) -> None:
        self._git_label.setText(f"  {branch}" if branch else "")

    def update_ops_count(self, n: int) -> None:
        self._ops_label.setText(f" {n} op(s) running" if n > 0 else "")

    def _subscribe_remote_events(self) -> None:
        from biome_fm.event_bus import RemoteConnected, RemoteDisconnected, RemoteSyncing
        from biome_fm.event_bus import bus as _bus
        _bus.subscribe(RemoteConnected, self._on_remote_connected)
        _bus.subscribe(RemoteDisconnected, self._on_remote_disconnected)
        _bus.subscribe(RemoteSyncing, self._on_remote_syncing)

    def _on_remote_connected(self, ev: object) -> None:
        scheme = getattr(ev, "scheme", "")
        host = getattr(ev, "host", "")
        self._remote_status_label.setText(f"  ● {scheme}://{host}")
        self._remote_status_label.show()

    def _on_remote_disconnected(self, ev: object) -> None:
        self._remote_status_label.hide()
        self._remote_status_label.setText("")

    def _on_remote_syncing(self, ev: object) -> None:
        active = getattr(ev, "active", False)
        if active:
            scheme = getattr(ev, "scheme", "")
            host = getattr(ev, "host", "")
            self._remote_status_label.setText(f"  ⧗ {scheme}://{host}")
            self._remote_status_label.show()
