"""Application bootstrap and DI wiring."""
from __future__ import annotations

import queue
import shlex
import subprocess
import threading
from pathlib import Path

from biome_fm.ai.provider import make_providers
from biome_fm.commands.base import CommandHistory
from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.config import load_config, save_config
from biome_fm.event_bus import (
    ActivePaneChanged,
    AsyncOpSubmitted,
    BookmarkChanged,
    EventBus,
    ShowHiddenToggled,
    ThemeChanged,
)
from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.models.vfs_router import VFSRouter
from biome_fm.operations.queue import OpQueue
from biome_fm.operations.task import OpCancelled, OpDone, OpError, OpProgress
from biome_fm.panel_manager import PanelManager
from biome_fm.plugins.builtin.dark_theme import BuiltinDarkTheme
from biome_fm.plugins.manager import PluginManager
from biome_fm.presenters.ai_presenter import AIPresenter
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter, PaneViewProtocol
from biome_fm.presenters.search_presenter import SearchPresenter, SearchResult
from biome_fm.presenters.settings_presenter import SettingsPresenter
from biome_fm.presenters.tabs_presenter import TabsPresenter
from biome_fm.preview.presenter import PreviewPresenter
from biome_fm.preview.providers.code import CodePreviewProvider
from biome_fm.preview.providers.fallback import FallbackProvider
from biome_fm.preview.providers.image import ImagePreviewProvider
from biome_fm.preview.providers.markdown import MarkdownPreviewProvider
from biome_fm.preview.providers.text import TextPreviewProvider
from biome_fm.preview.registry import PreviewRegistry
from biome_fm.qt import QApplication, QInputDialog, QKeySequence, QShortcut, QStandardPaths, QTimer
from biome_fm.session import (
    PanelSession,
    PaneSideState,
    SessionState,
    TabState,
    load_session,
    save_session,
)
from biome_fm.utils.opener import open_file
from biome_fm.utils.platform import reveal_in_finder
from biome_fm.views.ai_chat_panel import AIChatPanel
from biome_fm.views.bookmark_dialog import BookmarkDialog
from biome_fm.views.command_palette import CommandPalette
from biome_fm.views.main_window import MainWindow
from biome_fm.views.pane_side_view import PaneSideView
from biome_fm.views.panel_coordinator import PanelCoordinator
from biome_fm.views.preview_panel import PreviewPanel
from biome_fm.views.progress_dialog import ProgressDialog
from biome_fm.views.search_dialog import SearchDialog
from biome_fm.views.search_panel import SearchResultsPanel
from biome_fm.views.settings_dialog import SettingsDialog


def _config_dir() -> Path:
    loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(loc) / "biome-fm" if loc else Path.home() / ".config" / "biome-fm"


def _wire_pane(view: PaneViewProtocol, presenter: PanePresenter) -> None:
    """Connect PaneView signals to PanePresenter slots (non-preview only)."""
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


def create_app() -> MainWindow:
    # ── Config & Session ──────────────────────────────────────────
    cfg_dir = _config_dir()
    cfg = load_config(cfg_dir / "config.toml")
    session = load_session(cfg_dir / "session.json")

    # ── Plugins (before VFSRouter — passes plugin_manager in) ────────────────
    plugins = PluginManager()
    plugins.register_plugin(BuiltinDarkTheme())
    plugins.load_entry_points()
    plugins.load_local_plugins()

    from biome_fm.views.theme import apply_theme
    apply_theme(QApplication.instance(), cfg.theme, plugin_manager=plugins, glass=cfg.glass)  # type: ignore[arg-type]

    # ── Core services ─────────────────────────────────────────────
    vfs = VFSRouter(plugin_manager=plugins)
    bus = EventBus()
    history = CommandHistory()
    store = BookmarkStore(cfg_dir / "bookmarks.toml")
    op_queue = OpQueue(max_workers=2)

    # ── Tabs + Panes ──────────────────────────────────────────────
    left_side = PaneSideView()
    right_side = PaneSideView()
    left_tabs = TabsPresenter(vfs, left_side, left_side.new_pane, opener=open_file)
    right_tabs = TabsPresenter(vfs, right_side, right_side.new_pane, opener=open_file)

    # ── Preview (early — needed by _wire_preview, called during restore) ──
    preview_registry = PreviewRegistry()
    for _p in [
        ImagePreviewProvider(), MarkdownPreviewProvider(),
        CodePreviewProvider(), TextPreviewProvider(), FallbackProvider(),
    ]:
        preview_registry.register(_p)
    preview_panel = PreviewPanel()
    preview_presenter = PreviewPresenter(view=preview_panel, registry=preview_registry)
    preview_presenter.set_dark("dark" in cfg.theme.lower())

    coord: PanelCoordinator | None = None  # late-bound; set after window creation

    def _wire_preview(view: object) -> None:
        sig = getattr(view, "view_requested", None)
        if sig is not None:
            def _on_view(p: object = view) -> None:
                if coord is None:
                    return
                item = p.current_item() if hasattr(p, "current_item") else None  # type: ignore[union-attr]
                if item is not None and item.name != "..":
                    preview_presenter.render_item(item)
                coord.toggle("preview", manager.active_pane_id)
            sig.connect(_on_view)
        sig2 = getattr(view, "cursor_changed", None)
        if sig2 is not None:
            sig2.connect(preview_presenter.update_if_visible)

    def _restore(tabs: TabsPresenter, state: PaneSideState) -> None:
        for ts in state.tabs:
            p = tabs.new_tab(Path(ts.path))
            v = tabs.view_at(tabs.tab_count - 1)
            _wire_pane(v, p)
            _wire_preview(v)
        tabs.switch_tab(state.active_idx)

    home = Path.home()
    if session:
        _restore(left_tabs, session.left)
        _restore(right_tabs, session.right)
    else:
        lp = left_tabs.new_tab(home)
        v0 = left_tabs.view_at(0)
        _wire_pane(v0, lp)
        _wire_preview(v0)
        rp = right_tabs.new_tab(home)
        v1 = right_tabs.view_at(0)
        _wire_pane(v1, rp)
        _wire_preview(v1)

    # ── Manager ───────────────────────────────────────────────────
    manager = ManagerPresenter(
        left=left_tabs, right=right_tabs, vfs=vfs,  # type: ignore[arg-type]
        history=history, bus=bus, config=cfg, op_queue=op_queue,
    )
    _progress_dialogs: dict[int, ProgressDialog] = {}

    # ── Wire DnD for existing tabs ────────────────────────────────────────────
    def _wire_dnd(view: object, pane_id: str) -> None:
        sig = getattr(view, "files_dropped", None)
        if sig is not None:
            pid = pane_id
            sig.connect(lambda p, m, f, _pid=pid: manager.drop_files(p, _pid, m, f))

    for _pid, _tabs in [("left", left_tabs), ("right", right_tabs)]:
        for _i in range(_tabs.tab_count):
            _wire_dnd(_tabs.view_at(_i), _pid)

    providers = make_providers(cfg)
    _model_fields = {
        "claude":       "ai_claude_model",
        "openai":       "ai_openai_model",
        "ollama":       "ai_ollama_model",
        "claude-code":  "ai_cli_claude_code_model",
        "codex":        "ai_cli_codex_model",
        "opencode":     "ai_cli_opencode_model",
    }
    for _pname, _p in providers.items():
        _field = _model_fields.get(_pname)
        if _field:
            _saved = getattr(cfg, _field, "")
            if _saved and _saved in _p.models:
                _p.set_model(_saved)
    ai_panel = AIChatPanel()
    ai_presenter = AIPresenter(view=ai_panel, providers=providers,
                               default_provider=cfg.ai_default_provider)
    ai_panel.message_submitted.connect(ai_presenter.send)
    ai_panel.provider_changed.connect(ai_presenter.switch_provider)
    def _on_provider_changed(name: str) -> None:
        cfg.ai_default_provider = name
        save_config(cfg, cfg_dir / "config.toml")
    ai_panel.provider_changed.connect(_on_provider_changed)
    ai_panel.model_changed.connect(ai_presenter.switch_model)
    ai_panel.cancel_requested.connect(ai_presenter.cancel)
    ai_panel.attachment_dropped.connect(ai_presenter.add_attachment)
    ai_panel._context_bar.chip_removed.connect(ai_presenter.remove_attachment)

    def _on_ai_model_changed(model: str) -> None:
        field = _model_fields.get(ai_presenter._active_key)
        if field:
            setattr(cfg, field, model)
            save_config(cfg, cfg_dir / "config.toml")

    ai_panel.model_changed.connect(_on_ai_model_changed)

    def _on_ai_navigate(path_str: str) -> None:
        path = Path(path_str).expanduser()
        if not path.is_absolute():
            path = (_active().current_path / path_str)
        path = path.resolve()
        if not path.exists():
            return
        inactive = right_tabs if manager.active_pane_id == "left" else left_tabs
        target = path if path.is_dir() else path.parent
        inactive.navigate_to(target)
        if path.is_file():
            v = inactive.view_at(inactive.active_idx)
            if hasattr(v, "select_item"):
                v.select_item(path.name)

    ai_panel.file_link_clicked.connect(_on_ai_navigate)
    # Init provider list in UI
    if providers:
        default = cfg.ai_default_provider
        key = default if default in providers else next(iter(providers))
        p = providers[key]
        ai_panel.set_provider_list(list(providers), key, p.models, p.active_model)

    search_panel = SearchResultsPanel()

    # ── Window ────────────────────────────────────────────────────
    window = MainWindow(left_side, right_side, ai_panel, preview_panel)
    _glass_active = cfg.glass  # actual enable happens in __main__ after show()
    window._glass_cfg = cfg.glass
    if cfg.glass:
        from biome_fm.views.glass_style import mark_glass
        mark_glass(window, recursive=True)
    window.splitter.addWidget(search_panel)
    search_panel.hide()

    panel_mgr = PanelManager()
    coord = PanelCoordinator(
        panel_mgr,
        panels={"preview": preview_panel, "ai": ai_panel, "search": search_panel},
        left_side=left_side,
        right_side=right_side,
        splitter=window.splitter,
        main_window=window,
    )

    window.preview_toggle_requested.connect(lambda: coord.toggle("preview", manager.active_pane_id))
    window.ai_toggle_requested.connect(lambda: coord.toggle("ai", manager.active_pane_id))

    def _on_panel_state_changed(name: str, state: str) -> None:
        visible = state != "hidden"
        if name == "preview":
            window._act_preview.setChecked(visible)
        elif name == "ai":
            window._act_ai.setChecked(visible)
    coord.state_changed.connect(_on_panel_state_changed)

    preview_panel.detach_requested.connect(lambda: coord.detach("preview"))
    preview_panel.close_requested.connect(lambda: coord.toggle("preview"))
    ai_panel.detach_requested.connect(lambda: coord.detach("ai"))
    ai_panel.close_requested.connect(lambda: coord.toggle("ai"))
    window.detach_preview_requested.connect(lambda: coord.detach("preview"))
    window.detach_ai_requested.connect(lambda: coord.detach("ai"))

    def _init_layout() -> None:
        window.splitter.setSizes([600, 600, 0, 0, 0])
        if session:
            coord.restore_state({
                "preview": {
                    "state": session.preview.state,
                    "float_geometry": session.preview.float_geometry,
                },
                "ai": {"state": session.ai.state, "float_geometry": session.ai.float_geometry},
            })
        v = left_tabs.view_at(left_tabs.active_idx)
        if hasattr(v, "_table"):
            v._table.setFocus()

    QTimer.singleShot(0, _init_layout)

    drain_timer = QTimer(window)
    drain_timer.setInterval(50)
    drain_timer.timeout.connect(ai_presenter.drain)
    drain_timer.start()

    preview_timer = QTimer(window)
    preview_timer.setInterval(100)
    preview_timer.timeout.connect(preview_presenter.drain)
    preview_timer.start()

    # ── Op queue drain ────────────────────────────────────────────
    def _drain_op_events() -> None:
        for event in op_queue.drain():
            dlg = _progress_dialogs.get(event.task_id)  # type: ignore[attr-defined]
            if isinstance(event, OpProgress):
                if dlg:
                    dlg.update_progress(event)
            elif isinstance(event, OpDone):
                cmd = manager.pop_pending_cmd(event.task_id)
                if cmd is not None:
                    history.push(cmd)
                manager._refresh_both()
                if dlg:
                    dlg.mark_done()
                    _progress_dialogs.pop(event.task_id, None)
            elif isinstance(event, OpError):
                manager._refresh_both()
                if dlg:
                    dlg.mark_error(event.error)
                    _progress_dialogs.pop(event.task_id, None)
            elif isinstance(event, OpCancelled):
                manager._refresh_both()
                if dlg:
                    dlg.mark_cancelled()
                    _progress_dialogs.pop(event.task_id, None)

    def _on_async_op(ev: AsyncOpSubmitted) -> None:
        dlg = ProgressDialog(ev.task_id, ev.description, window)
        dlg.set_cancel_callback(lambda: op_queue.cancel(ev.task_id))
        _progress_dialogs[ev.task_id] = dlg
        dlg.show()

    bus.subscribe(AsyncOpSubmitted, _on_async_op)

    op_timer = QTimer(window)
    op_timer.setInterval(50)
    op_timer.timeout.connect(_drain_op_events)
    op_timer.start()

    # ── Active side helper ────────────────────────────────────────
    def _active() -> TabsPresenter:
        return left_tabs if manager.active_pane_id == "left" else right_tabs

    def _run_cmd(cmd: str) -> None:
        subprocess.Popen(shlex.split(cmd), cwd=str(_active().current_path))

    window.command_submitted.connect(_run_cmd)

    # ── Search ────────────────────────────────────────────────────
    _search_presenter: SearchPresenter | None = None
    _search_queue: queue.SimpleQueue[SearchResult | None] = queue.SimpleQueue()
    _CANCELLED = object()

    def _on_search_requested() -> None:
        nonlocal _search_presenter, _search_queue
        if _search_presenter is not None:
            _search_presenter.cancel()
        _search_queue = queue.SimpleQueue()
        params = SearchDialog.get_params(_active().current_path, window)
        if params is None:
            return
        query, mode, max_results = params
        _search_presenter = SearchPresenter(vfs, _active().current_path)
        search_panel.on_search_started(query)
        coord.toggle("search", manager.active_pane_id)
        q = _search_queue

        def _run() -> None:
            _search_presenter.search(  # type: ignore[union-attr]
                query, mode=mode, max_results=max_results,
                on_match=q.put,
            )
            sentinel = _CANCELLED if _search_presenter._cancel.is_set() else None  # type: ignore[union-attr]
            q.put(sentinel)

        threading.Thread(target=_run, daemon=True).start()

    def _drain_search() -> None:
        batch: list[SearchResult] = []
        done = False
        cancelled = False
        try:
            while True:
                item = _search_queue.get_nowait()
                if item is None:
                    done = True
                    break
                if item is _CANCELLED:
                    done = True
                    cancelled = True
                    break
                batch.append(item)
        except queue.Empty:
            pass
        if batch:
            search_panel.add_results(batch)
        if done:
            if cancelled:
                search_panel.on_cancelled()
            else:
                search_panel.on_finished(search_panel.result_count)

    search_timer = QTimer(window)
    search_timer.setInterval(50)
    search_timer.timeout.connect(_drain_search)
    search_timer.start()

    window.search_requested.connect(_on_search_requested)
    search_panel.close_requested.connect(lambda: coord.toggle("search", manager.active_pane_id))
    search_panel.stop_requested.connect(
        lambda: _search_presenter.cancel() if _search_presenter else None
    )
    search_panel.detach_requested.connect(lambda: coord.detach("search"))

    def _on_navigate_to_file(parent_dir: object, filename: str) -> None:
        tabs = _active()
        tabs.navigate_to(parent_dir)  # type: ignore[arg-type]
        v = tabs.view_at(tabs.active_idx)
        if hasattr(v, "select_item"):
            v.select_item(filename)  # type: ignore[union-attr]

    search_panel.navigate_to_file.connect(_on_navigate_to_file)

    # ── New tab ───────────────────────────────────────────────────
    def _new_tab() -> None:
        side = _active()
        pid = "left" if side is left_tabs else "right"
        p = side.new_tab(side.current_path)
        v = side.view_at(side.tab_count - 1)
        _wire_pane(v, p)
        _wire_preview(v)
        _wire_ctx(v)
        _wire_plugin_ctx(v, pid)
        _wire_bm(v, side)
        _wire_dnd(v, pid)

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

    def _reveal_in_finder() -> None:
        target = _active().current_item()
        if target is not None:
            reveal_in_finder(target.path)

    def _wire_plugin_ctx(view: object, pane_id: str) -> None:
        if hasattr(view, "plugin_menu_extra"):
            _pid = pane_id
            view.plugin_menu_extra = lambda: [  # type: ignore[attr-defined]
                a for lst in plugins.hook.context_menu_actions(items=[], pane_id=_pid)
                for a in lst
            ]

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
                preview_presenter.render_item(_active().current_item())
                coord.toggle("preview", manager.active_pane_id)
            elif action == "open_finder":
                _reveal_in_finder()
            elif action == "add_bookmark":
                item = _active().current_item()
                if item and item.name != "..":
                    store.add(item.path)
                else:
                    store.add(_active().current_path)
                bus.publish(BookmarkChanged())
        sig = getattr(view, "context_action_requested", None)
        if sig is not None:
            sig.connect(_dispatch)

    # Wire ctx for existing tabs
    for _pid2, _tabs2 in [("left", left_tabs), ("right", right_tabs)]:
        for _i2 in range(_tabs2.tab_count):
            _v2 = _tabs2.view_at(_i2)
            _wire_ctx(_v2)
            _wire_plugin_ctx(_v2, _pid2)

    # ── Bookmarks ──────────────────────────────────────────────────
    _bm_dialog: BookmarkDialog | None = None

    def _open_bm_dialog() -> None:
        nonlocal _bm_dialog
        if _bm_dialog is None or not _bm_dialog.isVisible():
            _bm_dialog = BookmarkDialog(store, bus, window)
            _bm_dialog.show()
        else:
            _bm_dialog._refresh()
            _bm_dialog.raise_()
            _bm_dialog.activateWindow()

    def _wire_bm(view: object, tabs: TabsPresenter) -> None:
        if hasattr(view, "set_bookmark_store"):
            view.set_bookmark_store(store)  # type: ignore[union-attr]
        sig = getattr(view, "bookmark_chosen", None)
        if sig is not None:
            def _on_bm(path: Path, _tabs=tabs) -> None:
                target = path if path.is_dir() else path.parent
                _tabs.navigate_to(target)
                if not path.is_dir():
                    v = _tabs.view_at(_tabs.active_idx)
                    if hasattr(v, "select_item"):
                        v.select_item(path.name)
            sig.connect(_on_bm)
        sig2 = getattr(view, "edit_bookmarks_requested", None)
        if sig2 is not None:
            sig2.connect(_open_bm_dialog)

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
    QShortcut(QKeySequence("Ctrl+H"), window).activated.connect(manager.toggle_hidden)
    QShortcut(QKeySequence("Ctrl+Shift+F"), window).activated.connect(_on_search_requested)

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

    def _switch_pane() -> None:
        manager.switch_active_pane()
        target = right_tabs if manager.active_pane_id == "right" else left_tabs
        v = target.view_at(target.active_idx)
        if hasattr(v, "_table"):
            v._table.setFocus()  # type: ignore[attr-defined]

    window.tab_shortcut.activated.connect(_switch_pane)

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
    QShortcut(QKeySequence("Alt+["),     window).activated.connect(lambda: _active().go_back())
    QShortcut(QKeySequence("Alt+]"),     window).activated.connect(lambda: _active().go_forward())

    # ── Misc shortcuts ────────────────────────────────────────────
    def _toggle_preview_f3() -> None:
        if coord is None:
            return
        item = _active().current_item()
        if item is not None and item.name != "..":
            preview_presenter.render_item(item)
        coord.toggle("preview", manager.active_pane_id)

    bar.view_requested.connect(_toggle_preview_f3)
    QShortcut(QKeySequence("Ctrl+Shift+C"), window).activated.connect(_copy_path)
    QShortcut(QKeySequence("F3"),           window).activated.connect(_toggle_preview_f3)
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

    def _all_proxies():
        for tabs in (left_tabs, right_tabs):
            for v in tabs._views:
                p = getattr(v, "_proxy", None)
                if p is not None:
                    yield p

    def _on_show_hidden(ev: ShowHiddenToggled) -> None:
        for proxy in _all_proxies():
            proxy.set_show_hidden(ev.enabled)
        save_config(cfg, cfg_dir / "config.toml")

    bus.subscribe(ShowHiddenToggled, _on_show_hidden)

    if cfg.show_hidden:
        for proxy in _all_proxies():
            proxy.set_show_hidden(True)

    def _on_theme_changed(ev: ThemeChanged) -> None:
        for side in (left_side, right_side):
            side.style().unpolish(side)
            side.style().polish(side)
        # Update preview dark flag based on theme name
        preview_presenter.set_dark("dark" in ev.name.lower())

    from biome_fm.event_bus import bus as global_bus  # theme events use module-level bus
    global_bus.subscribe(ThemeChanged, _on_theme_changed)

    # ── Focus tracking → active pane ─────────────────────────────
    def _on_focus_changed(old: object, new: object) -> None:
        if new is None:
            return
        if left_side.isAncestorOf(new):  # type: ignore[arg-type]
            manager.set_active_pane("left")
        elif right_side.isAncestorOf(new):  # type: ignore[arg-type]
            manager.set_active_pane("right")

    QApplication.instance().focusChanged.connect(_on_focus_changed)  # type: ignore[union-attr]

    # ── Settings ─────────────────────────────────────────────────
    def _open_settings() -> None:
        themes_dir = Path(__file__).parent / "themes"
        available_themes = sorted(p.stem for p in themes_dir.glob("*.toml"))
        plugin_names = [p["name"] for p in plugins.get_installed_plugins()]
        dlg = SettingsDialog(window)
        old_theme = cfg.theme
        presenter = SettingsPresenter(
            cfg, dlg,
            available_themes=available_themes,
            available_plugins=plugin_names,
        )
        if dlg.exec():
            presenter.apply()
            from biome_fm.views.theme import apply_theme
            apply_theme(QApplication.instance(), cfg.theme, plugin_manager=plugins, glass=cfg.glass)
            # apply_theme already publishes ThemeChanged(name, tokens) via global bus
            nonlocal _glass_active
            from biome_fm.views.glass import disable_glass, enable_glass, prepare_glass
            if cfg.glass and not _glass_active:
                from biome_fm.views.glass_style import GlassStyle, mark_glass
                QApplication.instance().setStyle(GlassStyle())
                mark_glass(window, recursive=True)
                prepare_glass(window)
                enable_glass(window)
                _glass_active = True
            elif not cfg.glass and _glass_active:
                disable_glass(window)
                from biome_fm.views.glass_style import unmark_glass
                unmark_glass(window, recursive=True)
                QApplication.instance().setStyle("Fusion")
                _glass_active = False
            bus.publish(ShowHiddenToggled(enabled=cfg.show_hidden))
            save_config(cfg, cfg_dir / "config.toml")

    # ── Command palette ───────────────────────────────────────────
    registry = CommandRegistry()
    plugins.call_register_commands(registry)
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
        CommandEntry("Toggle AI",      "Ctrl+I",       lambda: coord.toggle("ai", manager.active_pane_id)),  # noqa: E501
        CommandEntry("Refresh",        "Ctrl+R",       lambda: _active().refresh()),
        CommandEntry("Copy Path",      "Ctrl+Shift+C", _copy_path),
        CommandEntry("Preview",        "F3",           _toggle_preview_f3),
        CommandEntry("Sync Browsing",  "Ctrl+Shift+L", manager.toggle_mirror),
        CommandEntry("Toggle Hidden",  "Ctrl+H",       manager.toggle_hidden),
        CommandEntry("Back",           "Alt+Left",     lambda: _active().go_back()),
        CommandEntry("Forward",        "Alt+Right",    lambda: _active().go_forward()),
        CommandEntry("Up",             "Alt+Up",       lambda: _active().go_up()),
        CommandEntry("Home",           "Alt+Home",     lambda: _active().go_home()),
        CommandEntry("Settings",         "Ctrl+,",       _open_settings),
        CommandEntry("Find Files",       "Ctrl+Shift+F", _on_search_requested),
    ]:
        registry.register(entry)

    palette = CommandPalette(registry, parent=window)
    QShortcut(QKeySequence("Ctrl+P"), window).activated.connect(palette.open)
    QShortcut(QKeySequence("Ctrl+,"), window).activated.connect(_open_settings)
    window.settings_requested.connect(_open_settings)

    # ── Save on close ─────────────────────────────────────────────
    def _on_close() -> None:
        panel_states = coord.save_state()
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
                preview=PanelSession(**panel_states.get("preview", {})),
                ai=PanelSession(**panel_states.get("ai", {})),
            ),
            cfg_dir / "session.json",
        )
        cfg.splitter_sizes = window.splitter_sizes
        _close_field = _model_fields.get(ai_presenter._active_key)
        if _close_field:
            setattr(cfg, _close_field, ai_presenter._provider.active_model)
        save_config(cfg, cfg_dir / "config.toml")
        ai_presenter.shutdown()
        drain_timer.stop()
        preview_presenter.shutdown()
        preview_timer.stop()
        search_timer.stop()
        op_timer.stop()
        op_queue.shutdown(wait=False)

    window.about_to_close.connect(_on_close)
    window._refs = (manager, left_tabs, right_tabs, ai_presenter, drain_timer, plugins,  # type: ignore[attr-defined]
                    preview_presenter, preview_timer, coord, panel_mgr,
                    op_queue, op_timer, search_timer)

    return window
