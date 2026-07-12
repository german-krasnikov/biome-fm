"""Application bootstrap and DI wiring."""
from __future__ import annotations

import subprocess
from pathlib import Path

from biome_fm.ai.provider import make_provider
from biome_fm.commands.base import CommandHistory
from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.config import load_config, save_config
from biome_fm.event_bus import ActivePaneChanged, BookmarkChanged, EventBus
from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.models.vfs_router import VFSRouter
from biome_fm.plugins.manager import PluginManager
from biome_fm.presenters.ai_presenter import AIPresenter
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter, PaneViewProtocol
from biome_fm.presenters.tabs_presenter import TabsPresenter
from biome_fm.qt import QApplication, QInputDialog, QKeySequence, QShortcut, QStandardPaths, QTimer
from biome_fm.session import PaneSideState, SessionState, TabState, load_session, save_session
from biome_fm.utils.opener import open_file
from biome_fm.utils.platform import quick_look_item, reveal_in_finder
from biome_fm.views.ai_chat_panel import AIChatPanel
from biome_fm.views.bookmark_dialog import BookmarkDialog
from biome_fm.views.command_palette import CommandPalette
from biome_fm.views.main_window import MainWindow
from biome_fm.views.pane_side_view import PaneSideView


def _config_dir() -> Path:
    loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(loc) / "biome-fm" if loc else Path.home() / ".config" / "biome-fm"


def _wire_pane(view: PaneViewProtocol, presenter: PanePresenter) -> None:
    """Connect PaneView signals to PanePresenter slots."""
    view.item_activated.connect(presenter.on_item_activated)  # type: ignore[attr-defined]
    view.path_change_requested.connect(presenter.navigate_to)  # type: ignore[attr-defined]
    view.mark_toggle_requested.connect(presenter.toggle_mark)  # type: ignore[attr-defined]
    for attr, slot in [
        ("back_requested", presenter.go_back),
        ("forward_requested", presenter.go_forward),
        ("up_requested", presenter.go_up),
        ("home_requested", presenter.go_home),
        ("mark_toggle_up_requested", presenter.toggle_mark_up),
    ]:
        sig = getattr(view, attr, None)
        if sig is not None:
            sig.connect(slot)
    sig = getattr(view, "view_requested", None)
    if sig is not None:
        sig.connect(lambda p=presenter: quick_look_item(p.current_item()))


def create_app() -> MainWindow:
    # ── Config & Session ──────────────────────────────────────────
    cfg_dir = _config_dir()
    cfg = load_config(cfg_dir / "config.toml")
    session = load_session(cfg_dir / "session.json")

    # ── Core services ─────────────────────────────────────────────
    vfs = VFSRouter()
    bus = EventBus()
    history = CommandHistory()
    store = BookmarkStore(cfg_dir / "bookmarks.toml")

    # ── Tabs + Panes ──────────────────────────────────────────────
    left_side = PaneSideView()
    right_side = PaneSideView()
    left_tabs = TabsPresenter(vfs, left_side, left_side.new_pane, opener=open_file)
    right_tabs = TabsPresenter(vfs, right_side, right_side.new_pane, opener=open_file)

    def _restore(tabs: TabsPresenter, state: PaneSideState) -> None:
        for ts in state.tabs:
            p = tabs.new_tab(Path(ts.path))
            _wire_pane(tabs.view_at(tabs.tab_count - 1), p)
        tabs.switch_tab(state.active_idx)

    home = Path.home()
    if session:
        _restore(left_tabs, session.left)
        _restore(right_tabs, session.right)
    else:
        lp = left_tabs.new_tab(home)
        _wire_pane(left_tabs.view_at(0), lp)
        rp = right_tabs.new_tab(home)
        _wire_pane(right_tabs.view_at(0), rp)

    # ── Manager ───────────────────────────────────────────────────
    manager = ManagerPresenter(
        left=left_tabs, right=right_tabs, vfs=vfs,  # type: ignore[arg-type]
        history=history, bus=bus,
    )

    # ── Wire DnD for existing tabs ────────────────────────────────────────────
    for _pid, _tabs in [("left", left_tabs), ("right", right_tabs)]:
        for _i in range(_tabs.tab_count):
            _v = _tabs.view_at(_i)
            sig = getattr(_v, "files_dropped", None)
            if sig is not None:
                sig.connect(lambda paths, move, pid=_pid: manager.drop_files(paths, pid, move))

    ai_provider = make_provider(cfg.ai_api_key)
    ai_panel = AIChatPanel()
    ai_presenter = AIPresenter(view=ai_panel, provider=ai_provider)
    ai_panel.message_submitted.connect(ai_presenter.send)

    # ── Window ────────────────────────────────────────────────────
    window = MainWindow(left_side, right_side, ai_panel)

    drain_timer = QTimer(window)
    drain_timer.setInterval(100)
    drain_timer.timeout.connect(ai_presenter.drain)
    drain_timer.start()

    # ── Active side helper ────────────────────────────────────────
    def _active() -> TabsPresenter:
        return left_tabs if manager.active_pane_id == "left" else right_tabs

    def _run_cmd(cmd: str) -> None:
        subprocess.Popen(cmd, shell=True, cwd=str(_active().current_path))

    window.command_submitted.connect(_run_cmd)

    # ── New tab ───────────────────────────────────────────────────
    def _new_tab() -> None:
        side = _active()
        pid = "left" if side is left_tabs else "right"
        p = side.new_tab(side.current_path)
        v = side.view_at(side.tab_count - 1)
        _wire_pane(v, p)
        _wire_ctx(v)
        _wire_bm(v, side)
        sig = getattr(v, "files_dropped", None)
        if sig is not None:
            sig.connect(lambda paths, move, _pid=pid: manager.drop_files(paths, _pid, move))

    # ── Dialog helpers ────────────────────────────────────────────
    def _ask_mkdir() -> None:
        name, ok = QInputDialog.getText(window, "New Folder", "Name:")
        if ok and name.strip():
            manager.mkdir(name.strip())

    def _ask_rename() -> None:
        item = _active().current_item()
        if item is None or item.name == "..":
            return
        name, ok = QInputDialog.getText(window, "Rename", "New name:", text=item.name)
        if ok and name.strip() and name.strip() != item.name:
            manager.rename(item, name.strip())

    def _copy_path() -> None:
        item = _active().current_item()
        path = str(item.path) if item is not None else str(_active().current_path)
        QApplication.clipboard().setText(path)

    def _quick_look() -> None:
        quick_look_item(_active().current_item())

    def _reveal_in_finder() -> None:
        target = _active().current_item()
        if target is not None:
            reveal_in_finder(target.path)

    def _wire_ctx(view: object) -> None:
        def _dispatch(action: str) -> None:
            items = _active().marked_items
            if action == "copy":
                manager.copy_selected(items)
            elif action == "move":
                manager.move_selected(items)
            elif action == "delete":
                manager.delete_selected(items)
            elif action == "rename":
                _ask_rename()
            elif action == "copy_path":
                _copy_path()
            elif action == "quick_look":
                _quick_look()
            elif action == "open_finder":
                _reveal_in_finder()
        sig = getattr(view, "context_action_requested", None)
        if sig is not None:
            sig.connect(_dispatch)

    # Wire ctx for existing tabs
    for _pid2, _tabs2 in [("left", left_tabs), ("right", right_tabs)]:
        for _i2 in range(_tabs2.tab_count):
            _wire_ctx(_tabs2.view_at(_i2))

    # ── Bookmarks ──────────────────────────────────────────────────
    def _wire_bm(view: object, tabs: TabsPresenter) -> None:
        if hasattr(view, "set_bookmark_store"):
            view.set_bookmark_store(store)  # type: ignore[union-attr]
        sig = getattr(view, "bookmark_chosen", None)
        if sig is not None:
            sig.connect(tabs.navigate_to)
        sig2 = getattr(view, "edit_bookmarks_requested", None)
        if sig2 is not None:
            sig2.connect(lambda: BookmarkDialog(store, bus, window).exec())

    for _tabs_bm in (left_tabs, right_tabs):
        for _i_bm in range(_tabs_bm.tab_count):
            _wire_bm(_tabs_bm.view_at(_i_bm), _tabs_bm)

    def _bookmark_toggle() -> None:
        path = _active().current_path
        if path in store:
            store.remove(path)
        else:
            store.add(path)
        bus.publish(BookmarkChanged())

    QShortcut(QKeySequence("Ctrl+D"), window).activated.connect(_bookmark_toggle)

    # ── Shortcuts ─────────────────────────────────────────────────
    QShortcut(QKeySequence("Ctrl+T"), window).activated.connect(_new_tab)
    QShortcut(QKeySequence("Ctrl+W"), window).activated.connect(
        lambda: _active().close_tab(_active().active_idx)
    )

    # ── Tab bar ───────────────────────────────────────────────────
    left_side.tab_close_requested.connect(left_tabs.close_tab)
    left_side.tab_changed.connect(left_tabs.switch_tab)
    right_side.tab_close_requested.connect(right_tabs.close_tab)
    right_side.tab_changed.connect(right_tabs.switch_tab)

    # ── Action bar ────────────────────────────────────────────────
    bar = window.action_bar
    bar.copy_requested.connect(lambda: manager.copy_selected(_active().marked_items))
    bar.move_requested.connect(lambda: manager.move_selected(_active().marked_items))
    bar.delete_requested.connect(lambda: manager.delete_selected(_active().marked_items))
    bar.mkdir_requested.connect(_ask_mkdir)
    bar.rename_requested.connect(_ask_rename)
    bar.exit_requested.connect(window.close)
    window.tab_shortcut.activated.connect(manager.switch_active_pane)

    # ── Nav signals from MainWindow toolbar ───────────────────────
    for attr, slot in [
        ("back_requested", lambda: _active().go_back()),
        ("forward_requested", lambda: _active().go_forward()),
        ("up_requested", lambda: _active().go_up()),
        ("home_requested", lambda: _active().go_home()),
    ]:
        sig = getattr(window, attr, None)
        if sig is not None:
            sig.connect(slot)

    # ── Alt nav shortcuts ─────────────────────────────────────────
    QShortcut(QKeySequence("Alt+Left"),  window).activated.connect(lambda: _active().go_back())
    QShortcut(QKeySequence("Alt+Right"), window).activated.connect(lambda: _active().go_forward())
    QShortcut(QKeySequence("Alt+Up"),    window).activated.connect(lambda: _active().go_up())
    QShortcut(QKeySequence("Alt+Home"),  window).activated.connect(lambda: _active().go_home())

    # ── Misc shortcuts ────────────────────────────────────────────
    QShortcut(QKeySequence("Ctrl+Shift+C"), window).activated.connect(_copy_path)
    QShortcut(QKeySequence("F3"),           window).activated.connect(_quick_look)
    QShortcut(QKeySequence("Ctrl+Z"),       window).activated.connect(manager.undo)
    QShortcut(QKeySequence("Ctrl+Shift+Z"), window).activated.connect(manager.redo)
    QShortcut(QKeySequence("Ctrl+Shift+L"), window).activated.connect(manager.toggle_mirror)

    # ── Undo/Redo from menu ───────────────────────────────────────
    window.undo_requested.connect(manager.undo)
    window.redo_requested.connect(manager.redo)

    # ── Toolbar signals ───────────────────────────────────────────
    window.refresh_requested.connect(lambda: _active().refresh())
    window.new_tab_requested.connect(_new_tab)

    # ── Active pane border ────────────────────────────────────────
    def _on_active_changed(event: ActivePaneChanged) -> None:
        left_side.set_active(event.pane_id == "left")
        right_side.set_active(event.pane_id == "right")

    bus.subscribe(ActivePaneChanged, _on_active_changed)
    left_side.set_active(True)
    right_side.set_active(False)

    # ── Focus tracking → active pane ─────────────────────────────
    def _on_focus_changed(old: object, new: object) -> None:
        if new is None:
            return
        if left_side.isAncestorOf(new):  # type: ignore[arg-type]
            manager.set_active_pane("left")
        elif right_side.isAncestorOf(new):  # type: ignore[arg-type]
            manager.set_active_pane("right")

    QApplication.instance().focusChanged.connect(_on_focus_changed)  # type: ignore[union-attr]

    # ── Plugins ───────────────────────────────────────────────────
    plugins = PluginManager()
    plugins.load_entry_points()

    # ── Command palette ───────────────────────────────────────────
    registry = CommandRegistry()
    plugins.register_commands(registry)
    for entry in [
        CommandEntry("Copy",           "F5",           lambda: bar.copy_requested.emit()),
        CommandEntry("Move",           "F6",           lambda: bar.move_requested.emit()),
        CommandEntry("Make Directory", "F7",           lambda: bar.mkdir_requested.emit()),
        CommandEntry("Delete",         "F8",           lambda: bar.delete_requested.emit()),
        CommandEntry("Rename",         "F9",           lambda: bar.rename_requested.emit()),
        CommandEntry("Undo",           "Ctrl+Z",       manager.undo),
        CommandEntry("Redo",           "Ctrl+Shift+Z", manager.redo),
        CommandEntry("Switch Pane",    "Tab",          manager.switch_active_pane),
        CommandEntry("Quit",           "Alt+F4",       window.close),  # type: ignore[arg-type]
        CommandEntry("New Tab",        "Ctrl+T",       _new_tab),
        CommandEntry("Close Tab",      "Ctrl+W",       lambda: _active().close_tab(_active().active_idx)),  # noqa: E501
        CommandEntry("Toggle AI",      "Ctrl+I",       window.toggle_ai_panel),
        CommandEntry("Refresh",        "Ctrl+R",       lambda: _active().refresh()),
        CommandEntry("Copy Path",      "Ctrl+Shift+C", _copy_path),
        CommandEntry("Quick Look",     "F3",           _quick_look),
        CommandEntry("Sync Browsing",  "Ctrl+Shift+L", manager.toggle_mirror),
        CommandEntry("Back",           "Alt+Left",     lambda: _active().go_back()),
        CommandEntry("Forward",        "Alt+Right",    lambda: _active().go_forward()),
        CommandEntry("Up",             "Alt+Up",       lambda: _active().go_up()),
        CommandEntry("Home",           "Alt+Home",     lambda: _active().go_home()),
    ]:
        registry.register(entry)

    palette = CommandPalette(registry, parent=window)
    QShortcut(QKeySequence("Ctrl+P"), window).activated.connect(palette.open)

    # ── Save on close ─────────────────────────────────────────────
    def _on_close() -> None:
        save_session(
            SessionState(
                left=PaneSideState(
                    tabs=[TabState(str(p)) for p in left_tabs.paths()],
                    active_idx=left_tabs.active_idx,
                ),
                right=PaneSideState(
                    tabs=[TabState(str(p)) for p in right_tabs.paths()],
                    active_idx=right_tabs.active_idx,
                ),
            ),
            cfg_dir / "session.json",
        )
        cfg.splitter_sizes = window.splitter_sizes
        save_config(cfg, cfg_dir / "config.toml")
        ai_presenter.shutdown()
        drain_timer.stop()

    window.about_to_close.connect(_on_close)
    window._refs = (manager, left_tabs, right_tabs, ai_presenter, drain_timer, plugins)  # type: ignore[attr-defined]

    return window
