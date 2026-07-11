"""Application bootstrap and DI wiring."""
from __future__ import annotations

from pathlib import Path

from biome_fm.ai.provider import make_provider
from biome_fm.commands.base import CommandHistory
from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.config import load_config, save_config
from biome_fm.event_bus import EventBus
from biome_fm.models.vfs_router import VFSRouter
from biome_fm.plugins.manager import PluginManager
from biome_fm.presenters.ai_presenter import AIPresenter
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter, PaneViewProtocol
from biome_fm.presenters.tabs_presenter import TabsPresenter
from biome_fm.qt import QInputDialog, QKeySequence, QShortcut, QStandardPaths, QTimer
from biome_fm.session import PaneSideState, SessionState, TabState, load_session, save_session
from biome_fm.views.ai_chat_panel import AIChatPanel
from biome_fm.views.command_palette import CommandPalette
from biome_fm.views.main_window import MainWindow
from biome_fm.views.pane_side_view import PaneSideView


def _config_dir() -> Path:
    loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(loc) / "biome-fm" if loc else Path.home() / ".config" / "biome-fm"


def _wire_pane(view: PaneViewProtocol, presenter: PanePresenter) -> None:
    """Connect PaneView signals to PanePresenter slots."""
    view.item_activated.connect(presenter.on_item_activated)  # type: ignore[union-attr]
    view.path_change_requested.connect(presenter.navigate_to)  # type: ignore[union-attr]
    view.mark_toggle_requested.connect(presenter.toggle_mark)  # type: ignore[union-attr]


def create_app() -> MainWindow:
    # ── Config & Session ──────────────────────────────────────────
    cfg_dir = _config_dir()
    cfg = load_config(cfg_dir / "config.toml")
    session = load_session(cfg_dir / "session.json")

    # ── Core services ─────────────────────────────────────────────
    vfs = VFSRouter()
    bus = EventBus()
    history = CommandHistory()

    # ── Tabs + Panes ──────────────────────────────────────────────
    left_side = PaneSideView()
    right_side = PaneSideView()
    left_tabs = TabsPresenter(vfs, left_side, left_side.new_pane)
    right_tabs = TabsPresenter(vfs, right_side, right_side.new_pane)

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

    # ── AI ────────────────────────────────────────────────────────
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

    # ── New tab ───────────────────────────────────────────────────
    def _new_tab() -> None:
        side = _active()
        _wire_pane(side.view_at(side.tab_count - 1), side.new_tab(side.current_path))

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
        CommandEntry("Quit",           "Alt+F4",       window.close),
        CommandEntry("New Tab",        "Ctrl+T",       _new_tab),
        CommandEntry("Close Tab",      "Ctrl+W",       lambda: _active().close_tab(_active().active_idx)),  # noqa: E501
        CommandEntry("Toggle AI",      "Ctrl+I",       window.toggle_ai_panel),
        CommandEntry("Refresh",        "Ctrl+R",       lambda: _active().refresh()),
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
