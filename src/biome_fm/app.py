"""Application bootstrap and DI wiring."""
from __future__ import annotations

import os
import shlex
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from biome_fm.ai.provider import make_providers
from biome_fm.commands.base import CommandHistory
from biome_fm.commands.editor_rename_cmd import EditorRenameCmd
from biome_fm.commands.git_stage import GitStageCmd, GitUnstageCmd
from biome_fm.commands.new_file_cmd import NewFileCmd
from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.commands.trash_cmd import TrashCmd
from biome_fm.config import load_config, save_config
from biome_fm.event_bus import (
    ActivePaneChanged,
    AsyncOpSubmitted,
    BookmarkChanged,
    OperationFinished,
    OperationStarted,
    ShowHiddenToggled,
    SyncBrowsingToggled,
    ThemeChanged,
    bus,
)
from biome_fm.git.status_cache import GitStatusCache, RepoStatus
from biome_fm.git.worker import GitStatusWorker
from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.models.clipboard_service import ClipboardService
from biome_fm.models.command_store import CommandStore
from biome_fm.models.dir_state_store import DirStateStore
from biome_fm.models.frecency_store import FrecencyStore
from biome_fm.models.highlight_rules import HighlightRule
from biome_fm.models.project_detector import detect_project
from biome_fm.models.search_template_store import SearchTemplateStore
from biome_fm.models.session_store import SessionStore
from biome_fm.models.tag_store import TagStore
from biome_fm.models.user_actions import UserActionsStore
from biome_fm.models.vfs_router import VFSRouter
from biome_fm.models.workspace_store import WorkspaceStore
from biome_fm.operations.queue import OpQueue, make_serial_queue
from biome_fm.operations.task import OpCancelled, OpConflict, OpDone, OpError, OpProgress
from biome_fm.panel_manager import PanelManager
from biome_fm.plugins.builtin.dark_theme import BuiltinDarkTheme
from biome_fm.plugins.manager import PluginManager
from biome_fm.plugins.types import ActionSpec
from biome_fm.presenters.ai_presenter import AIPresenter
from biome_fm.presenters.info_presenter import InfoPresenter
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter, PaneViewProtocol
from biome_fm.presenters.search_coordinator import SearchCoordinator
from biome_fm.presenters.settings_presenter import SettingsPresenter
from biome_fm.presenters.tabs_presenter import TabsPresenter
from biome_fm.preview.presenter import PreviewPresenter
from biome_fm.preview.providers.archive import ArchivePreviewProvider
from biome_fm.preview.providers.code import CodePreviewProvider
from biome_fm.preview.providers.fallback import FallbackProvider
from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
from biome_fm.preview.providers.git_log import GitLogPreviewProvider
from biome_fm.preview.providers.hex import HexPreviewProvider
from biome_fm.preview.providers.image import ImagePreviewProvider
from biome_fm.preview.providers.json_tree import JsonTreeProvider
from biome_fm.preview.providers.markdown import MarkdownPreviewProvider
from biome_fm.preview.providers.metadata import MetadataPreviewProvider
from biome_fm.preview.providers.pdf import PDFPreviewProvider
from biome_fm.preview.providers.text import TextPreviewProvider
from biome_fm.preview.providers.video import VideoPreviewProvider
from biome_fm.preview.registry import PreviewRegistry
from biome_fm.qt import (
    QApplication,
    QDialog,
    QInputDialog,
    QKeySequence,
    QMessageBox,
    QShortcut,
    QStandardPaths,
    Qt,
    QTimer,
)
from biome_fm.session import (
    PanelSession,
    PaneSideState,
    SessionState,
    TabState,
    load_session,
    save_session,
)
from biome_fm.utils.opener import open_file, open_in_editor
from biome_fm.utils.platform import open_terminal, reveal_in_finder
from biome_fm.utils.shell_vars import expand_shell_vars
from biome_fm.utils.watcher import WatchService
from biome_fm.views.ai_chat_panel import AIChatPanel
from biome_fm.views.bookmark_dialog import BookmarkDialog
from biome_fm.views.command_palette import CommandPalette
from biome_fm.views.confirm_dialog import ConfirmDialog
from biome_fm.views.conflict_dialog import ConflictDialog
from biome_fm.views.fullscreen_viewer import FullscreenViewer
from biome_fm.views.fuzzy_finder import FuzzyFinder
from biome_fm.views.highlight_rules_dialog import HighlightRulesDialog
from biome_fm.views.info_panel import InfoPanel
from biome_fm.views.main_window import MainWindow
from biome_fm.views.nl_ops_dialog import NLOpsDialog
from biome_fm.views.pane_side_view import PaneSideView
from biome_fm.views.panel_coordinator import PanelCoordinator
from biome_fm.views.pattern_dialog import PatternDialog
from biome_fm.views.preview_panel import PreviewPanel
from biome_fm.views.progress_dialog import ProgressDialog
from biome_fm.views.search_panel import SearchResultsPanel
from biome_fm.views.session_picker_dialog import SessionPickerDialog
from biome_fm.views.settings_dialog import SettingsDialog
from biome_fm.views.terminal_panel import TerminalPanel
from biome_fm.views.transfer_queue_panel import TransferQueuePanel
from biome_fm.views.workspace_dialog import WorkspaceDialog

# ── Module-level constants ────────────────────────────────────────────────────

_AI_MODEL_FIELDS: dict[str, str] = {
    "claude":       "ai_claude_model",
    "openai":       "ai_openai_model",
    "ollama":       "ai_ollama_model",
    "claude-code":  "ai_cli_claude_code_model",
    "codex":        "ai_cli_codex_model",
    "opencode":     "ai_cli_opencode_model",
}


def _should_show_notification(ev: OperationFinished, *, has_active_window: bool) -> bool:
    """Return True if a tray notification should be shown for this event."""
    return ev.success and not has_active_window


class _OpsCounter:
    """Tracks in-progress operations and notifies a callback on change."""
    def __init__(self, update_fn: Callable[[int], None]) -> None:
        self._count = 0
        self._update = update_fn

    def inc(self) -> None:
        self._count += 1
        self._update(self._count)

    def dec(self) -> None:
        self._count = max(0, self._count - 1)
        self._update(self._count)


def _get_git_branch(path: Path) -> str:
    """Return current git branch for path, or empty string if not in a repo."""
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "branch", "--show-current"],
            capture_output=True, text=True, timeout=2,
        )
        return r.stdout.strip()
    except Exception:
        return ""


@dataclass
class _AppContext:
    """Keeps references alive for the lifetime of the window."""
    manager: object
    left_tabs: object
    right_tabs: object
    ai_presenter: object
    preview_presenter: object
    info_presenter: object
    coord: object
    panel_mgr: object
    op_queue: object
    plugins: object
    git_worker: object = None
    timers: list = field(default_factory=list)
    tray: object = None  # F320 — keep QSystemTrayIcon alive
    hotkey_listener: object = None  # F321 — keep pynput listener alive


def _build_tray(window: object) -> object:
    """F320 — Create system tray icon with Show/Hide + Quit context menu."""
    from PySide6.QtWidgets import QMenu, QSystemTrayIcon
    tray = QSystemTrayIcon(window)  # type: ignore[arg-type]
    menu = QMenu()
    menu.addAction("Show/Hide", lambda: (
        window.hide() if window.isVisible() else (window.show(), window.raise_())  # type: ignore[union-attr]
    ))
    menu.addAction("Quit", lambda: __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication.quit())
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason, w=window: (
        w.show() or w.raise_()  # type: ignore[union-attr]
    ) if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    tray.show()
    return tray


# ── Module-level build functions (construction only, no signal wiring) ────────

def _apply_zoom(app: object, cfg: object, cfg_path: "Path", system_pt: int, delta: int) -> None:
    """F408 — Adjust app font size by delta pts; delta=0 resets to system default."""
    if delta == 0:
        pt = system_pt
    else:
        current = app.font().pointSize()  # type: ignore[union-attr]
        if current <= 0:
            current = 11
        pt = max(7, min(32, current + delta))
    f = app.font()  # type: ignore[union-attr]
    f.setPointSize(pt)
    app.setFont(f)  # type: ignore[union-attr]
    cfg.ui_font_size = 0 if pt == system_pt else pt  # type: ignore[union-attr]
    save_config(cfg, cfg_path)  # type: ignore[arg-type]


def _write_last_dir(path: Path | None) -> None:
    """Write *path* to the file named by BIOME_LAST_DIR_FILE (shell cd-on-exit helper)."""
    dest = os.environ.get("BIOME_LAST_DIR_FILE")
    if not dest or not path:
        return
    s = str(path)
    if ":/" in s:  # VFS / non-local path (Path normalises sftp:// → sftp:/)
        return
    try:
        Path(dest).write_text(s)
    except OSError:
        pass


def _config_dir() -> Path:
    loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    return Path(loc) / "biome-fm" if loc else Path.home() / ".config" / "biome-fm"


def _build_plugins(cfg):
    """Construct and configure PluginManager, apply initial theme."""
    from biome_fm.views.theme import apply_theme
    plugins = PluginManager()
    plugins.register_plugin(BuiltinDarkTheme())
    plugins.load_entry_points()
    _loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    plugins.load_local_plugins(Path(_loc) / "biome-fm" / "plugins" if _loc else None)
    apply_theme(
        QApplication.instance(), cfg.theme,
        plugin_manager=plugins, glass=cfg.glass, glass_opacity=cfg.glass_opacity,
    )  # type: ignore[arg-type]
    return plugins


def _build_panes(vfs, store: DirStateStore | None = None, frecency: FrecencyStore | None = None):
    """Construct left/right PaneSideViews and TabsPresenters."""
    left_side = PaneSideView()
    right_side = PaneSideView()
    left_tabs = TabsPresenter(vfs, left_side, left_side.new_pane, opener=open_file, store=store, frecency=frecency)
    right_tabs = TabsPresenter(vfs, right_side, right_side.new_pane, opener=open_file, store=store, frecency=frecency)
    return left_side, right_side, left_tabs, right_tabs


def _build_preview(cfg):
    """Construct PreviewRegistry, PreviewPanel, PreviewPresenter."""
    preview_registry = PreviewRegistry()
    for _p in [
        ImagePreviewProvider(), MarkdownPreviewProvider(), VideoPreviewProvider(),
        JsonTreeProvider(), CodePreviewProvider(), TextPreviewProvider(), FallbackProvider(),
    ]:
        preview_registry.register(_p)
    preview_panel = PreviewPanel()
    preview_presenter = PreviewPresenter(view=preview_panel, registry=preview_registry)
    preview_presenter.set_dark("dark" in cfg.theme.lower())
    if cfg.glass:
        from biome_fm.views.theme import _glass_alphas
        _, _sel = _glass_alphas(cfg.glass_opacity)
        preview_panel.set_code_alpha(_sel)
    return preview_registry, preview_panel, preview_presenter


def _build_ai(cfg, cfg_dir: Path):
    """Construct AI providers, AIChatPanel, AIPresenter. No signal wiring."""
    providers = make_providers(cfg)
    for pname, p in providers.items():
        field_name = _AI_MODEL_FIELDS.get(pname)
        if field_name:
            saved = getattr(cfg, field_name, "")
            if saved and saved in p.models:
                p.set_model(saved)
    ai_panel = AIChatPanel()
    ai_presenter = AIPresenter(view=ai_panel, providers=providers,
                               default_provider=cfg.ai_default_provider)
    if providers:
        default = cfg.ai_default_provider
        key = default if default in providers else next(iter(providers))
        p = providers[key]
        ai_panel.set_provider_list(list(providers), key, p.models, p.active_model)
    return providers, ai_panel, ai_presenter


def _pad_sizes(sizes: list[int], count: int) -> list[int]:
    """Pad/truncate saved splitter sizes to exactly `count` entries (extras are 0)."""
    return (sizes + [0] * count)[:count]


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
        ("mark_at_requested", presenter.toggle_mark_at),
        ("calculate_dir_sizes_requested", presenter.calculate_all_dir_sizes),
    ]:
        sig = getattr(view, attr, None)
        if sig is not None:
            sig.connect(slot)
    sig = getattr(view, "mark_range_requested", None)
    if sig is not None:
        sig.connect(lambda a, t, p=presenter: p.mark_range(a.path, t.path))
    sig = getattr(view, "history_jump_requested", None)
    if sig is not None:
        sig.connect(presenter.navigate_to)


def _wire_ai_cursor(view: object, tabs: object, ai_presenter: object) -> None:
    """Connect cursor_changed → ai_presenter.set_context."""
    sig = getattr(view, "cursor_changed", None)
    if sig is None:
        return
    sig.connect(lambda item, t=tabs, ap=ai_presenter: ap.set_context(
        t.current_path, [item] if item is not None else []
    ))


def _wire_info_cursor(view: object, ip: object) -> None:
    """Connect cursor_changed → info_presenter.on_cursor_changed."""
    sig = getattr(view, "cursor_changed", None)
    if sig is not None:
        sig.connect(ip.on_cursor_changed)


def _update_recent_dirs(cfg: object, path: Path) -> None:
    """Prepend path to cfg.recent_dirs, dedup, limit 50."""
    s = str(path)
    dirs = [d for d in cfg.recent_dirs if d != s]
    dirs.insert(0, s)
    cfg.recent_dirs = dirs[:50]


def _wire_recent_dirs(view: object, cfg: object) -> None:
    """Connect path_updated → _update_recent_dirs."""
    sig = getattr(view, "path_updated", None)
    if sig is not None:
        sig.connect(lambda path, c=cfg: _update_recent_dirs(c, path))


def _wire_system_theme(cfg: object, style_hints: object, apply_fn: object) -> None:
    """Connect colorSchemeChanged → apply_fn if cfg.follow_system_theme."""
    if not cfg.follow_system_theme:
        return
    sig = getattr(style_hints, "colorSchemeChanged", None)
    if sig is not None:
        sig.connect(apply_fn)


def _handle_app_state_change(state: object, watch_timer: object, refresh_timer: object, drain: object) -> None:
    """Pause/resume watch timers based on app focus state."""
    from biome_fm.qt import Qt
    if state == Qt.ApplicationState.ApplicationActive:
        watch_timer.start()  # type: ignore[union-attr]
        refresh_timer.start()  # type: ignore[union-attr]
        drain()  # type: ignore[operator]
    else:
        watch_timer.stop()  # type: ignore[union-attr]
        refresh_timer.stop()  # type: ignore[union-attr]


def create_app() -> MainWindow:
    # ── Config & Session ──────────────────────────────────────────
    cfg_dir = _config_dir()
    cfg = load_config(cfg_dir / "config.toml")
    session = load_session(cfg_dir / "session.json")

    # F308 — apply configurable font size before any widgets are created
    # F408 — capture system default before any override
    _app = QApplication.instance()
    _system_pt = (_app.font().pointSize() if _app is not None and _app.font().pointSize() > 0 else 11)
    if cfg.ui_font_size > 0:
        if _app is not None:
            _f = _app.font()
            _f.setPointSize(cfg.ui_font_size)
            _app.setFont(_f)

    # ── Construction phase ────────────────────────────────────────
    plugins = _build_plugins(cfg)
    vfs = VFSRouter(plugin_manager=plugins)
    history = CommandHistory()
    clipboard = ClipboardService()
    store = BookmarkStore(cfg_dir / "bookmarks.toml")
    tag_store = TagStore.load(cfg_dir / "tags.toml")
    user_actions_store = UserActionsStore(cfg_dir / "actions.json")
    user_actions_store.load()
    _project_actions: list = []  # updated on navigate; shared by closure
    ws_store = WorkspaceStore(cfg_dir / "workspaces.json")
    named_session_store = SessionStore(cfg_dir / "sessions.json")
    op_queue = make_serial_queue() if cfg.serial_ops else OpQueue(max_workers=2)
    dir_state_store = DirStateStore(cfg_dir / "dir_state.json")
    frecency_store = FrecencyStore(cfg_dir / "frecency.json")
    from biome_fm.presenters.file_collector import FileCollector
    file_collector = FileCollector()
    left_side, right_side, left_tabs, right_tabs = _build_panes(vfs, dir_state_store, frecency_store)
    import queue as _queue_mod
    _watch_queue: _queue_mod.SimpleQueue = _queue_mod.SimpleQueue()
    left_watcher = WatchService(callback=_watch_queue.put)
    right_watcher = WatchService(callback=_watch_queue.put)
    preview_registry, preview_panel, preview_presenter = _build_preview(cfg)
    git_cache = GitStatusCache()
    git_worker = GitStatusWorker(git_cache)
    from biome_fm.preview.providers.sqlite_preview import SqlitePreviewProvider
    for _p4 in [GitDiffPreviewProvider(status_fn=git_cache.file_status),
                GitLogPreviewProvider(), GitBlamePreviewProvider(),
                ArchivePreviewProvider(), PDFPreviewProvider(),
                MetadataPreviewProvider(), HexPreviewProvider(), SqlitePreviewProvider()]:
        preview_registry.register(_p4)
    try:
        from biome_fm.preview.providers.quicklook import QuickLookProvider
        preview_registry.register(QuickLookProvider())
    except ImportError:
        pass
    from biome_fm.preview.providers.script import load_script_providers
    for _sp in load_script_providers(cfg_dir / "preview_scripts"):
        preview_registry.register(_sp)
    for _pp in plugins.get_preview_providers():
        preview_registry.register(_pp)

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
            sig2.connect(lambda item, pp=preview_presenter: pp.update_if_visible(item) if cfg.auto_preview else None)

    def _wire_breadcrumb_completer(view: object) -> None:
        """Inject a remote-aware completion source into the breadcrumb path bar."""
        path_bar = getattr(view, "_path_bar", None)
        if path_bar is None or not hasattr(path_bar, "set_completer_source"):
            return

        def _remote_source(text: str) -> list[str]:
            if "://" not in text and ":/" not in text:
                return []
            try:
                p = Path(text) if text.endswith("/") else Path(text).parent
                items = vfs.listdir(p)
                base = str(p).rstrip("/")
                return [f"{base}/{item.name}" for item in items]
            except Exception:
                return []

        def _on_path_updated(path: Path) -> None:
            path_bar.set_completer_source(_remote_source if ":/" in str(path) else None)

        sig = getattr(view, "path_updated", None)
        if sig is not None:
            sig.connect(_on_path_updated)

    def _git_op(item: object, cmd_cls) -> None:
        p = getattr(item, "path", None)
        repo = git_cache.find_repo(p.parent) if p else None
        if repo is None:
            return
        history.execute(cmd_cls(p, repo))
        git_cache.invalidate(repo)
        git_worker.request(_active().current_path)
        manager._refresh_both()
    def _wire_git(view: object, watcher: WatchService) -> None:
        sig = getattr(view, "path_updated", None)
        if sig is not None:
            sig.connect(git_worker.request)
            sig.connect(watcher.set_path)
        if hasattr(view, "_git_status_fn"):
            view._git_status_fn = git_cache.file_status  # type: ignore[union-attr]
        for attr, cls in [("git_stage_requested", GitStageCmd), ("git_unstage_requested", GitUnstageCmd)]:
            s = getattr(view, attr, None)
            if s is not None:
                s.connect(lambda item, c=cls: _git_op(item, c))

    def _on_git_status(status: RepoStatus) -> None:
        if not cfg.show_git_status:
            return
        for _t in [left_tabs, right_tabs]:
            for _v in (_t.view_at(i) for i in range(_t.tab_count)):
                _m = getattr(_v, "_model", None)
                if _m and hasattr(_m, "set_git_status"):
                    _m.set_git_status(status.statuses, status.dirty_dirs)

    git_worker.status_ready.connect(_on_git_status)

    def _restore(tabs: TabsPresenter, state: PaneSideState) -> None:
        for ts in state.tabs:
            p = tabs.new_tab(Path(ts.path), deferred=True)  # lazy — load on first switch
            v = tabs.view_at(tabs.tab_count - 1)
            _wire_pane(v, p)
            _wire_preview(v)
            _wire_breadcrumb_completer(v)
        tabs.switch_tab(state.active_idx)  # triggers load of active tab

    home = Path.home()
    if session:
        _restore(left_tabs, session.left)
        _restore(right_tabs, session.right)
    else:
        lp = left_tabs.new_tab(home)
        v0 = left_tabs.view_at(0)
        _wire_pane(v0, lp)
        _wire_preview(v0)
        _wire_breadcrumb_completer(v0)
        rp = right_tabs.new_tab(home)
        v1 = right_tabs.view_at(0)
        _wire_pane(v1, rp)
        _wire_preview(v1)
        _wire_breadcrumb_completer(v1)

    # ── Manager ───────────────────────────────────────────────────
    _confirm_parent: list[object] = [None]  # late-bound after window creation
    manager = ManagerPresenter(
        left=left_tabs, right=right_tabs, vfs=vfs,  # type: ignore[arg-type]
        history=history, bus=bus, config=cfg, op_queue=op_queue,
        plugins=plugins,
        confirm=lambda spec: ConfirmDialog.confirm(
            spec.op, spec.sources, spec.dest, parent=_confirm_parent[0]
        ),
    )
    _progress_dialogs: dict[int, ProgressDialog] = {}

    # ── Per-view wire helpers (defined here; applied in single loop below) ────
    def _wire_dnd(view: object, pane_id: str) -> None:
        sig = getattr(view, "files_dropped", None)
        if sig is not None:
            pid = pane_id
            sig.connect(lambda p, m, f, _pid=pid: manager.drop_files(p, _pid, m, f))

    def _wire_new_tab(view: object, tabs) -> None:
        sig = getattr(view, "new_tab_requested", None)
        if sig is not None:
            sig.connect(lambda _tabs=tabs: _new_tab(_tabs))

    providers, ai_panel, ai_presenter = _build_ai(cfg, cfg_dir)

    # ── AI signal wiring ──────────────────────────────────────────
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
        field_name = _AI_MODEL_FIELDS.get(ai_presenter._active_key)
        if field_name:
            setattr(cfg, field_name, model)
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

    info_panel = InfoPanel()
    info_presenter = InfoPresenter(info_panel)

    search_panel = SearchResultsPanel()
    terminal_panel = TerminalPanel()

    # ── Window ────────────────────────────────────────────────────
    window = MainWindow(left_side, right_side, ai_panel, preview_panel)
    _confirm_parent[0] = window
    _glass_active = cfg.glass  # actual enable happens in __main__ after show()
    window._glass_cfg = cfg.glass
    if cfg.glass:
        from biome_fm.views.glass_style import mark_glass
        mark_glass(window, recursive=True)
    window.splitter.addWidget(search_panel)
    search_panel.hide()
    window.splitter.addWidget(terminal_panel)
    terminal_panel.hide()

    # ── Sidebar ───────────────────────────────────────────────────
    from PySide6.QtCore import QStorageInfo
    from PySide6.QtWidgets import QDockWidget

    from biome_fm.views.sidebar_panel import SidebarPanel
    _sidebar = SidebarPanel()
    _dock = QDockWidget("Sidebar", window)
    _dock.setWidget(_sidebar)
    _dock.setFeatures(
        QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
    )
    window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, _dock)
    _dock.hide()
    _volumes = [
        Path(v.rootPath())
        for v in QStorageInfo.mountedVolumes()
        if v.isValid() and v.isReady()
    ]
    _sidebar.set_volumes(_volumes)
    _sidebar.set_bookmarks(store.tree())
    bus.subscribe(BookmarkChanged, lambda _: _sidebar.set_bookmarks(store.tree()))

    def _on_project_navigate(path: Path) -> None:
        """F334/F337: detect project root, merge project bookmarks + actions."""
        proj = detect_project(path)
        proj_root = proj.root if proj else None
        proj_nodes = BookmarkStore.load_project(proj_root) if proj_root else []
        _sidebar.set_bookmarks(store.tree() + proj_nodes)
        _project_actions[:] = UserActionsStore.load_project(proj_root) if proj_root else []

    _sidebar.path_activated.connect(lambda p: manager.navigate_active(p))
    window.sidebar_toggle_requested.connect(lambda: _dock.setVisible(not _dock.isVisible()))
    QShortcut(QKeySequence("Ctrl+B"), window).activated.connect(
        lambda: _dock.setVisible(not _dock.isVisible())
    )

    xfer_panel = TransferQueuePanel(op_queue.cancel, window)
    xfer_panel.setWindowFlags(Qt.WindowType.Tool)
    xfer_panel.resize(420, 280)
    xfer_panel.setWindowTitle("Transfer Queue")
    xfer_panel.hide()

    panel_mgr = PanelManager()
    coord = PanelCoordinator(
        panel_mgr,
        panels={"preview": preview_panel, "ai": ai_panel, "search": search_panel, "terminal": terminal_panel, "info": info_panel},
        left_side=left_side,
        right_side=right_side,
        splitter=window.splitter,
        main_window=window,
    )

    window.preview_toggle_requested.connect(lambda: coord.toggle("preview", manager.active_pane_id))
    window.ai_toggle_requested.connect(lambda: coord.toggle("ai", manager.active_pane_id))

    def _toggle_terminal() -> None:
        terminal_panel.start(_active().current_path)
        coord.toggle("terminal", manager.active_pane_id)

    window.terminal_requested.connect(_toggle_terminal)
    QShortcut(QKeySequence("Ctrl+`"), window).activated.connect(_toggle_terminal)

    def _on_panel_state_changed(name: str, state: str) -> None:
        visible = state != "hidden"
        if name == "preview":
            window._act_preview.setChecked(visible)
        elif name == "ai":
            window._act_ai.setChecked(visible)
    coord.state_changed.connect(_on_panel_state_changed)

    preview_panel.detach_requested.connect(lambda: coord.detach("preview"))
    preview_panel.close_requested.connect(lambda: coord.toggle("preview"))
    preview_panel.mode_changed.connect(preview_presenter.set_mode)
    preview_panel.tail_toggled.connect(preview_presenter.set_tail_mode)
    preview_panel.summarize_requested.connect(
        lambda: ai_presenter.summarize_file(_active().current_item()) if _active().current_item() is not None else None  # noqa: E501
    )
    ai_panel.detach_requested.connect(lambda: coord.detach("ai"))
    ai_panel.close_requested.connect(lambda: coord.toggle("ai"))
    terminal_panel.detach_requested.connect(lambda: coord.detach("terminal"))
    terminal_panel.close_requested.connect(lambda: coord.toggle("terminal"))
    terminal_panel.cwd_changed.connect(lambda p: manager.navigate_active(p) if p.is_dir() else None)
    # Sync terminal cwd + project context when any pane navigates
    for _side_tabs in [left_tabs, right_tabs]:
        for _i in range(_side_tabs.tab_count):
            _sig = getattr(_side_tabs.view_at(_i), "path_updated", None)
            if _sig is not None:
                _sig.connect(terminal_panel.set_cwd)
                _sig.connect(_on_project_navigate)
    window.detach_preview_requested.connect(lambda: coord.detach("preview"))
    window.detach_ai_requested.connect(lambda: coord.detach("ai"))

    def _init_layout() -> None:
        window.splitter.setSizes(_pad_sizes(cfg.splitter_sizes, window.splitter.count()))
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

    def _drain_dir_sizes() -> None:
        for _tabs in (left_tabs, right_tabs):
            for _i in range(_tabs.tab_count):
                _tabs.presenter_at(_i).drain_sizes()

    size_drain_timer = QTimer(window)
    size_drain_timer.setInterval(200)
    size_drain_timer.timeout.connect(_drain_dir_sizes)
    size_drain_timer.start()

    # ── Op queue drain ────────────────────────────────────────────
    def _drain_op_events() -> None:
        for event in op_queue.drain():
            dlg = _progress_dialogs.get(event.task_id)  # type: ignore[attr-defined]
            if isinstance(event, OpProgress):
                if dlg:
                    dlg.update_progress(event)
                xfer_panel.on_op_progress(
                    event.task_id, event.files_done, event.files_total,
                    event.bytes_done, event.bytes_total, event.current_file,
                )
            elif isinstance(event, OpDone):
                cmd = manager.pop_pending_cmd(event.task_id)
                if cmd is not None:
                    history.push(cmd)
                manager.fire_op_done(event.task_id)
                manager._refresh_both()
                if dlg:
                    dlg.mark_done()
                    _progress_dialogs.pop(event.task_id, None)
                xfer_panel.on_op_done(event.task_id)
            elif isinstance(event, OpError):
                manager._refresh_both()
                if dlg:
                    dlg.mark_error(event.error)
                    _progress_dialogs.pop(event.task_id, None)
                xfer_panel.on_op_error(event.task_id, str(event.error))
            elif isinstance(event, OpCancelled):
                manager._refresh_both()
                if dlg:
                    dlg.mark_cancelled()
                    _progress_dialogs.pop(event.task_id, None)
                xfer_panel.on_op_cancelled(event.task_id)
            elif isinstance(event, OpConflict):
                action = ConflictDialog.ask(event.src, event.dst, parent=window)
                event.resolver.reply(action)

    def _on_async_op(ev: AsyncOpSubmitted) -> None:
        dlg = ProgressDialog(ev.task_id, ev.description, window)
        dlg.set_cancel_callback(lambda: op_queue.cancel(ev.task_id))
        _progress_dialogs[ev.task_id] = dlg
        dlg.show()
        xfer_panel.on_op_started(ev.task_id, ev.description)
        xfer_panel.show()

    bus.subscribe(AsyncOpSubmitted, _on_async_op)

    # ── Tray notifications ────────────────────────────────────────
    from PySide6.QtWidgets import QSystemTrayIcon
    _tray = _build_tray(window)

    # F321 — global hotkey to summon window
    _hotkey_listener = None
    if cfg.global_hotkey:
        from biome_fm.utils.global_hotkey import register_global_hotkey
        def _summon() -> None:
            window.show()
            window.raise_()
        _hotkey_listener = register_global_hotkey(cfg.global_hotkey, _summon)

    def _on_op_finished(ev: OperationFinished) -> None:
        if _should_show_notification(ev, has_active_window=QApplication.activeWindow() is not None):
            _tray.showMessage("Biome FM", ev.description,
                              QSystemTrayIcon.MessageIcon.Information, 3000)

    bus.subscribe(OperationFinished, _on_op_finished)

    # ── Status bar: ops counter + git branch ─────────────────────
    _ops_ctr = _OpsCounter(window.update_ops_count)
    bus.subscribe(OperationStarted, lambda _ev: _ops_ctr.inc())

    def _on_op_finished_sb(ev: OperationFinished) -> None:
        _ops_ctr.dec()

    bus.subscribe(OperationFinished, _on_op_finished_sb)

    def _update_git_branch(path: Path) -> None:
        window.update_git_branch(_get_git_branch(path))

    op_timer = QTimer(window)
    op_timer.setInterval(50)
    op_timer.timeout.connect(_drain_op_events)
    op_timer.start()

    refresh_timer = QTimer(window)
    refresh_timer.setInterval(5000)
    refresh_timer.timeout.connect(
        lambda: manager._refresh_both() if not _progress_dialogs else None
    )
    refresh_timer.start()

    def _drain_watch_events() -> None:
        if _progress_dialogs:
            return
        while not _watch_queue.empty():
            try:
                changed_path = _watch_queue.get_nowait()
            except _queue_mod.Empty:
                break
            for _t in (left_tabs, right_tabs):
                if _t.current_path == changed_path:
                    _t.active.refresh()

    watch_timer = QTimer(window)
    watch_timer.setInterval(200)
    watch_timer.timeout.connect(_drain_watch_events)
    watch_timer.start()

    QApplication.instance().applicationStateChanged.connect(  # type: ignore[union-attr]
        lambda state: _handle_app_state_change(state, watch_timer, refresh_timer, _drain_watch_events)
    )

    # ── Active side helper ────────────────────────────────────────
    def _active() -> TabsPresenter:
        return left_tabs if manager.active_pane_id == "left" else right_tabs

    def _run_cmd(cmd: str) -> None:
        active = _active()
        other = right_tabs if manager.active_pane_id == "left" else left_tabs
        expanded = expand_shell_vars(
            cmd,
            files=[item.path for item in _op_items()],
            cwd=active.current_path,
            other_cwd=other.current_path,
        )
        subprocess.Popen(shlex.split(expanded), cwd=str(active.current_path))

    window.command_submitted.connect(_run_cmd)

    # ── Search ────────────────────────────────────────────────────
    _tmpl_store = SearchTemplateStore(cfg_dir / "search_templates.toml")

    def _on_search_completed(results) -> None:
        _active().navigate_virtual(
            [r.item for r in results], "Search Results",
            on_activate=lambda item: sc.navigate_to(item.path.parent, item.name),
        )

    def _on_search_history_update(h: list[str]) -> None:
        cfg.search_history = h
        save_config(cfg, cfg_dir / "config.toml")
        search_panel.set_history(h)

    sc = SearchCoordinator(
        vfs, coord, manager, search_panel, _active, window=window,
        on_search_completed=_on_search_completed,
        store=_tmpl_store,
        history=list(cfg.search_history),
        on_history_update=_on_search_history_update,
    )
    search_panel.set_history(list(cfg.search_history))
    search_panel.rerun_requested.connect(sc.request_search_with_query)
    window.search_requested.connect(sc.request_search)

    def _on_nl_op_requested() -> None:
        provider = ai_presenter._provider
        cwd = _active().current_path
        dlg = NLOpsDialog(provider=provider, cwd=cwd, parent=window)

        def _dispatch(op) -> None:
            if op.op in ("copy", "move") and op.sources:
                manager.drop_files(op.sources, manager.active_pane_id, op.op == "move", op.destination)
            elif op.op == "delete" and op.sources:
                items = [vfs.stat(p) for p in op.sources if p.exists()]
                manager.delete_selected(items)
            elif op.op == "mkdir" and op.destination:
                manager.mkdir(op.destination.name)

        dlg.execute_requested.connect(_dispatch)
        dlg.exec()

    window.nl_op_requested.connect(_on_nl_op_requested)

    def _on_shell_ops_requested(cmds: list[str]) -> None:
        provider = ai_presenter._provider
        cwd = _active().current_path
        dlg = NLOpsDialog(provider=provider, cwd=cwd,
                          prefill=cmds[0] if cmds else "", parent=window)

        def _dispatch(op) -> None:
            if op.op in ("copy", "move") and op.sources:
                manager.drop_files(op.sources, manager.active_pane_id, op.op == "move", op.destination)
            elif op.op == "delete" and op.sources:
                items = [vfs.stat(p) for p in op.sources if p.exists()]
                manager.delete_selected(items)
            elif op.op == "mkdir" and op.destination:
                manager.mkdir(op.destination.name)

        dlg.execute_requested.connect(_dispatch)
        dlg.exec()

    ai_panel.shell_ops_requested.connect(_on_shell_ops_requested)
    window.transfer_queue_requested.connect(
        lambda: xfer_panel.hide() if xfer_panel.isVisible() else xfer_panel.show()
    )
    window.flat_view_requested.connect(lambda: _active().toggle_flat_view())
    search_panel.stop_requested.connect(sc.cancel)
    search_panel.navigate_to_file.connect(sc.navigate_to)
    search_panel.close_requested.connect(lambda: coord.toggle("search", manager.active_pane_id))
    search_panel.detach_requested.connect(lambda: coord.detach("search"))
    search_panel.preview_requested.connect(preview_presenter.render_item)

    search_timer = QTimer(window)
    search_timer.setInterval(50)
    search_timer.timeout.connect(sc.drain)
    search_timer.start()

    # ── New tab ───────────────────────────────────────────────────
    def _new_tab(tabs=None) -> None:
        tabs = tabs or _active()
        pid = "left" if tabs is left_tabs else "right"
        watcher = left_watcher if tabs is left_tabs else right_watcher
        p = tabs.new_tab(tabs.current_path)
        v = tabs.view_at(tabs.tab_count - 1)
        _wire_pane(v, p)
        _wire_preview(v)
        _wire_ctx(v)
        _wire_plugin_ctx(v, pid)
        _wire_bm(v, tabs)
        _wire_dnd(v, pid)
        _wire_new_tab(v, tabs)
        _wire_git(v, watcher)
        _wire_tags(v)
        _wire_ai_rename(v)
        _wire_ai_context(v)
        _wire_ai_cursor(v, tabs, ai_presenter)
        _wire_info_cursor(v, info_presenter)
        _wire_recent_dirs(v, cfg)
        _wire_new_file(v)
        _wire_clipboard(v)
        _wire_trash(v)
        _wire_breadcrumb_completer(v)
        _sig = getattr(v, "path_updated", None)
        if _sig is not None:
            _sig.connect(terminal_panel.set_cwd)
            _sig.connect(_update_git_branch)
            _sig.connect(_on_project_navigate)

    def _dup_tab() -> None:
        """Duplicate the active tab — opens a new tab at the same path."""
        _new_tab()

    # ── Dialog helpers ────────────────────────────────────────────
    def _ask_mkdir() -> None:
        name, ok = QInputDialog.getText(window, "New Folder", "Name:")
        if ok and name.strip():
            manager.mkdir(name.strip())

    def _ask_new_file() -> None:
        name, ok = QInputDialog.getText(window, "New File", "File name:")
        if ok and name.strip():
            path = _active().current_path / name.strip()
            history.execute(NewFileCmd(path))
            manager._refresh_both()

    def _ask_rename() -> None:
        item = _active().current_item()
        if item is None or item.name == "..":
            return
        name, ok = QInputDialog.getText(window, "Rename", "New name:", text=item.name)
        if ok and name.strip() and name.strip() != item.name:
            manager.rename(item, name.strip())

    def _copy_path() -> None:
        items = _active().marked_items
        if items:
            QApplication.clipboard().setText("\n".join(str(i.path) for i in items))
        else:
            item = _active().current_item()
            path = str(item.path) if item is not None else str(_active().current_path)
            QApplication.clipboard().setText(path)

    def _copy_names() -> None:
        QApplication.clipboard().setText("\n".join(i.name for i in _op_items()))

    def _reveal_in_finder() -> None:
        target = _active().current_item()
        if target is not None:
            reveal_in_finder(target.path)

    def _op_items():
        items = _active().marked_items
        if items:
            return items
        cursor = _active().current_item()
        return [cursor] if cursor and cursor.name != ".." else []

    def _run_user_action(cmd: str) -> None:
        """F337: run a project user action in a shell subprocess."""
        import subprocess
        cwd = _active().current_path
        subprocess.Popen(cmd, shell=True, cwd=cwd)

    def _update_cut_state() -> None:
        cut = clipboard.has_cut
        for _tabs in (left_tabs, right_tabs):
            for _i in range(_tabs.tab_count):
                _v = _tabs.view_at(_i)
                _m = getattr(_v, "_model", None)
                if _m and hasattr(_m, "set_cut_paths"):
                    _m.set_cut_paths(cut)

    def _wire_clipboard(view: object) -> None:
        def _on_copy() -> None:
            clipboard.copy([i.path for i in _op_items()])
        def _on_cut() -> None:
            clipboard.cut([i.path for i in _op_items()])
            _update_cut_state()
        def _on_paste() -> None:
            paths, is_cut = clipboard.paste(_active().current_path)
            if not paths:
                return
            manager.drop_files(paths, manager.active_pane_id, is_cut)
            _update_cut_state()
        for _attr, _slot in [
            ("clipboard_copy_requested", _on_copy),
            ("clipboard_cut_requested", _on_cut),
            ("clipboard_paste_requested", _on_paste),
        ]:
            _sig = getattr(view, _attr, None)
            if _sig is not None:
                _sig.connect(_slot)

    def _wire_trash(view: object) -> None:
        def _on_trash() -> None:
            items = _op_items()
            if not items:
                return
            history.execute(TrashCmd([i.path for i in items]))
            manager._refresh_both()
        _sig = getattr(view, "trash_requested", None)
        if _sig is not None:
            _sig.connect(_on_trash)

    def _wire_plugin_ctx(view: object, pane_id: str) -> None:
        if hasattr(view, "plugin_menu_extra"):
            _pid = pane_id
            def _extras(_pid=_pid):
                plugin_actions = [
                    a for lst in plugins.hook.context_menu_actions(items=[], pane_id=_pid)
                    for a in lst
                ]
                proj = [
                    ActionSpec(label=a.label, callback=lambda cmd=a.command: _run_user_action(cmd))
                    for a in _project_actions
                ]
                return plugin_actions + proj
            view.plugin_menu_extra = _extras  # type: ignore[attr-defined]

    def _wire_ctx(view: object) -> None:
        def _dispatch(action: str) -> None:
            items = _op_items()
            if action == "copy":
                _do_copy_or_move("copy")
            elif action == "move":
                _do_copy_or_move("move")
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
            elif action == "checksum":
                from biome_fm.views.checksum_dialog import ChecksumDialog
                paths = [i.path for i in items if not i.is_dir]
                if paths:
                    ChecksumDialog(paths, window).show()
            elif action == "open_terminal":
                open_terminal(_active().current_path)
            elif action == "compress":
                if not items:
                    return
                name, ok = QInputDialog.getText(window, "Compress", "Archive name:", text="archive")
                if ok and name.strip():
                    n = name.strip()
                    if not n.endswith(".zip"):
                        n += ".zip"
                    manager.compress(items, _active().current_path / n)
            elif action == "extract":
                item = _active().current_item()
                if item:
                    manager.extract(item)
            elif action == "batch_rename":
                marked = _active().marked_items
                if len(marked) >= 2:
                    from biome_fm.views.batch_rename_dialog import BatchRenameDialog
                    dlg = BatchRenameDialog(marked, window)
                    if dlg.exec() == QDialog.DialogCode.Accepted and dlg.renames:
                        manager.multi_rename(dlg.renames)
            elif action == "batch_tag":
                marked = _active().marked_items
                if marked:
                    from biome_fm.commands.tag_cmd import TagCmd
                    from biome_fm.views.tag_dialog import TagDialog
                    current = tag_store.get_tags(marked[0].path)
                    result = TagDialog.get_tags(current, tag_store.all_tags(), parent=window)
                    if result is not None:
                        cmd = TagCmd([i.path for i in marked], add_tags=result, remove_tags=[], store=tag_store)
                        history.execute(cmd)
            elif action == "remove_quarantine":
                from biome_fm.commands.quarantine_cmd import RemoveQuarantineCmd
                cmd = RemoveQuarantineCmd([i.path for i in _op_items()])
                history.execute(cmd)
                _active().refresh()
        sig = getattr(view, "context_action_requested", None)
        if sig is not None:
            sig.connect(_dispatch)
        ren_sig = getattr(view, "inline_rename_requested", None)
        if ren_sig is not None:
            ren_sig.connect(lambda item, name: manager.rename(item, name))

    # ── Bookmarks ──────────────────────────────────────────────────
    _bm_dialog: BookmarkDialog | None = None

    def _nav_bm(path: Path, tabs: TabsPresenter) -> None:
        target = path if path.is_dir() else path.parent
        tabs.navigate_to(target)
        if not path.is_dir():
            v = tabs.view_at(tabs.active_idx)
            if hasattr(v, "select_item"):
                v.select_item(path.name)

    def _on_bm_dialog(path: Path) -> None:
        _nav_bm(path, _active())

    def _open_bm_dialog() -> None:
        nonlocal _bm_dialog
        if _bm_dialog is None or not _bm_dialog.isVisible():
            _bm_dialog = BookmarkDialog(store, bus, window)
            _bm_dialog.bookmark_chosen.connect(_on_bm_dialog)
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
                _nav_bm(path, _tabs)
            sig.connect(_on_bm)
        sig2 = getattr(view, "edit_bookmarks_requested", None)
        if sig2 is not None:
            sig2.connect(_open_bm_dialog)

    def _wire_tags(view: object) -> None:
        if hasattr(view, "set_tag_store"):
            view.set_tag_store(tag_store)  # type: ignore[union-attr]
        sig = getattr(view, "tag_requested", None)
        if sig is not None:
            def _on_tag_requested() -> None:
                from biome_fm.views.tag_dialog import TagDialog
                items = _op_items()
                if not items:
                    return
                # Use the first item's tags as current (intersection would be complex)
                current = tag_store.get_tags(items[0].path)
                result = TagDialog.get_tags(current, tag_store.all_tags(), parent=window)
                if result is not None:
                    from biome_fm.models.finder_tags import set_finder_tags
                    for item in items:
                        tag_store.set_tags(item.path, result)
                        set_finder_tags(item.path, result)
                    tag_store.save()
                    # Trigger model repaint
                    for _t in [left_tabs, right_tabs]:
                        for _i in range(_t.tab_count):
                            _v = _t.view_at(_i)
                            _m = getattr(_v, "_model", None)
                            if _m and hasattr(_m, "set_tag_store"):
                                _m.set_tag_store(tag_store)
            sig.connect(_on_tag_requested)

    def _wire_ai_rename(view: object) -> None:
        sig = getattr(view, "ai_rename_requested", None)
        if sig is None:
            return

        def _on_ai_rename_requested() -> None:
            from biome_fm.presenters.ai_rename_presenter import suggest_renames
            from biome_fm.views.ai_rename_dialog import AIRenameDialog

            items = _op_items()
            if not items:
                return
            provider = ai_presenter._provider
            names = [i.name for i in items]
            suggestions = suggest_renames(names, provider)
            dlg = AIRenameDialog(names, suggestions, parent=window)

            def _apply(pairs: list) -> None:
                item_by_name = {i.name: i for i in items}
                for original, new_name in pairs:
                    item = item_by_name.get(original)
                    if item:
                        manager.rename(item, new_name)

            dlg.rename_requested.connect(_apply)
            dlg.exec()

        sig.connect(_on_ai_rename_requested)

    def _wire_ai_context(view: object) -> None:
        sig = getattr(view, "ai_context_requested", None)
        if sig is None:
            return

        def _on_ai_context_requested() -> None:
            from biome_fm.views.ai_context_dialog import AIContextDialog

            items = _op_items()
            names = [i.name for i in items] if items else []
            provider = ai_presenter._provider
            dlg = AIContextDialog(names, provider, parent=window)
            dlg.exec()

        sig.connect(_on_ai_context_requested)

    def _wire_new_file(view: object) -> None:
        sig = getattr(view, "new_file_requested", None)
        if sig is not None:
            sig.connect(_ask_new_file)

    # ── Workspaces ─────────────────────────────────────────────────
    def _save_workspace(name: str) -> None:
        left_paths = [str(left_tabs.presenter_at(i).current_path) for i in range(left_tabs.tab_count)]
        right_paths = [str(right_tabs.presenter_at(i).current_path) for i in range(right_tabs.tab_count)]
        ws_store.save(name, left_paths, right_paths)

    def _load_workspace(name: str) -> None:
        data = ws_store.load(name)
        if not data:
            return
        for side_str, tabs in [("left", left_tabs), ("right", right_tabs)]:
            for i, p_str in enumerate(data.get(side_str, [])):
                path = Path(p_str)
                if not path.exists():
                    continue
                if i < tabs.tab_count:
                    tabs.presenter_at(i).navigate_to(path)
                else:
                    _new_tab(tabs)
                    tabs.presenter_at(tabs.tab_count - 1).navigate_to(path)

    def _open_workspace_dialog() -> None:
        dlg = WorkspaceDialog(ws_store, window)
        dlg.save_requested.connect(_save_workspace)
        dlg.load_requested.connect(_load_workspace)
        dlg.exec()

    # ── Single post-restore wire loop (DnD + new-tab + ctx + bm + git) ───────
    for _pid_w, _tabs_w, _watcher_w in [
        ("left", left_tabs, left_watcher),
        ("right", right_tabs, right_watcher),
    ]:
        for _i_w in range(_tabs_w.tab_count):
            _v_w = _tabs_w.view_at(_i_w)
            _wire_dnd(_v_w, _pid_w)
            _wire_new_tab(_v_w, _tabs_w)
            _wire_ctx(_v_w)
            _wire_plugin_ctx(_v_w, _pid_w)
            _wire_bm(_v_w, _tabs_w)
            _wire_git(_v_w, _watcher_w)
            _wire_tags(_v_w)
            _wire_ai_rename(_v_w)
            _wire_ai_context(_v_w)
            _wire_ai_cursor(_v_w, _tabs_w, ai_presenter)
            _wire_info_cursor(_v_w, info_presenter)
            _wire_recent_dirs(_v_w, cfg)
            _wire_new_file(_v_w)
            _wire_clipboard(_v_w)
            _wire_trash(_v_w)
            _pu = getattr(_v_w, "path_updated", None)
            if _pu is not None:
                _pu.connect(_update_git_branch)
                _pu.connect(_on_project_navigate)

    def _bookmark_toggle() -> None:
        path = _active().current_path
        if path in store:
            store.remove(path)
        else:
            store.add(path)
        bus.publish(BookmarkChanged())

    QShortcut(QKeySequence("Ctrl+D"), window).activated.connect(_bookmark_toggle)
    QShortcut(QKeySequence("Ctrl+H"), window).activated.connect(manager.toggle_hidden)
    QShortcut(QKeySequence("Ctrl+Shift+."), window).activated.connect(manager.toggle_hidden)
    QShortcut(QKeySequence("Ctrl+I"), window).activated.connect(
        lambda: coord.toggle("ai", manager.active_pane_id)
    )
    QShortcut(QKeySequence("Ctrl+Shift+F"), window).activated.connect(sc.request_search)
    QShortcut(QKeySequence("Ctrl+Shift+N"), window).activated.connect(_on_nl_op_requested)
    QShortcut(QKeySequence("Ctrl+Shift+T"), window).activated.connect(lambda: _active().toggle_flat_view())
    QShortcut(QKeySequence("Ctrl+."), window).activated.connect(lambda: manager.repeat_last(_op_items()))

    def _snapshot_session() -> SessionState:
        panel_states = coord.save_state()
        return SessionState(
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
        )

    def _save_named_session() -> None:
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(window, "Save Session", "Session name:")
        if ok and name.strip():
            named_session_store.save_named_session(name.strip(), _snapshot_session())

    def _open_session_picker() -> None:
        dlg = SessionPickerDialog(named_session_store, parent=window)
        if dlg.exec() and (name := getattr(dlg, "selected_name", None)):
            state = named_session_store.load_named_session(name)
            if state:
                _restore(left_tabs, state.left)
                _restore(right_tabs, state.right)

    QShortcut(QKeySequence("Ctrl+Shift+S"), window).activated.connect(_save_named_session)
    QShortcut(QKeySequence("Ctrl+Shift+O"), window).activated.connect(_open_session_picker)

    def _bulk_rename_editor() -> None:
        items = [i for i in _op_items() if i.name != ".."]
        if not items:
            return
        cmd = EditorRenameCmd(items, vfs)
        history.execute(cmd)
        manager._refresh_both()

    QShortcut(QKeySequence("Ctrl+Shift+R"), window).activated.connect(_bulk_rename_editor)

    def _select_by_pattern() -> None:
        dlg = PatternDialog(window)
        if dlg.exec():
            pattern, mode = dlg.result_values()
            if mode == "select":
                _active().select_by_pattern(pattern)
            else:
                _active().deselect_by_pattern(pattern)

    QShortcut(QKeySequence("Ctrl+G"), window).activated.connect(_select_by_pattern)

    def _select_by_criteria() -> None:
        from biome_fm.views.select_criteria_dialog import SelectByAttrDialog
        dlg = SelectByAttrDialog(window)
        if dlg.exec():
            _active().select_where(dlg.get_criteria().matches)

    QShortcut(QKeySequence("Ctrl+Shift+G"), window).activated.connect(_select_by_criteria)

    def _open_user_menu() -> None:
        from biome_fm.models.user_menu import load_user_menu
        from biome_fm.qt import QCursor, QMenu
        active = _active()
        other = right_tabs if manager.active_pane_id == "left" else left_tabs
        cwd = active.current_path
        commands = load_user_menu(cwd)
        if not commands:
            return
        menu = QMenu(window)
        for cmd in commands:
            label = f"{cmd.name}  [{cmd.shortcut}]" if cmd.shortcut else cmd.name
            action = menu.addAction(label)
            action.setData(cmd.command)
        chosen = menu.exec(QCursor.pos())
        if chosen:
            raw_cmd = chosen.data()
            expanded = expand_shell_vars(
                raw_cmd,
                files=[i.path for i in _op_items()],
                cwd=cwd,
                other_cwd=other.current_path,
            )
            subprocess.Popen(shlex.split(expanded), cwd=str(cwd))

    QShortcut(QKeySequence("F2"), window).activated.connect(_open_user_menu)

    def _open_quick_cd() -> None:
        from biome_fm.views.quick_cd_dialog import QuickCDDialog
        dlg = QuickCDDialog(frecency_store.top(50), _active().current_path, window)
        dlg.path_selected.connect(lambda p: _active().navigate_to(p))
        dlg.exec()

    QShortcut(QKeySequence("Alt+C"), window).activated.connect(_open_quick_cd)

    # ── Shortcuts ─────────────────────────────────────────────────
    def _open_jump_dialog() -> None:
        from biome_fm.views.jump_dialog import JumpDialog
        dlg = JumpDialog(frecency_store.top(20), parent=window)
        dlg.path_selected.connect(lambda p: _active().navigate_to(p))
        dlg.exec()

    QShortcut(QKeySequence("Ctrl+J"), window).activated.connect(_open_jump_dialog)
    QShortcut(QKeySequence("Ctrl+T"),     window).activated.connect(_new_tab)
    QShortcut(QKeySequence("Ctrl+Alt+T"), window).activated.connect(_dup_tab)

    def _collect_add() -> None:
        for item in _op_items():
            file_collector.add([item])
        window.statusBar().showMessage(f"Collection: {file_collector.count()} files", 2000)

    def _collect_show() -> None:
        file_collector.show(_active())

    QShortcut(QKeySequence("Ctrl+Alt+C"), window).activated.connect(_collect_add)
    QShortcut(QKeySequence("Ctrl+Alt+V"), window).activated.connect(_collect_show)

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
    _copy_history: list[str] = []

    def _do_copy_or_move(op: str) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog
        items = _op_items()
        if not items:
            return
        dest = manager.inactive_pane.current_path
        dlg = CopyMoveDialog(op, [i.path for i in items], dest, _copy_history, window)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        result = dlg.destination
        s = str(result)
        if s in _copy_history:
            _copy_history.remove(s)
        _copy_history.insert(0, s)
        del _copy_history[20:]
        if op == "copy":
            manager.copy_to(items, result, verify=dlg.verify_enabled)
        else:
            manager.move_to(items, result)

    bar.copy_requested.connect(lambda: _do_copy_or_move("copy"))
    bar.move_requested.connect(lambda: _do_copy_or_move("move"))
    bar.delete_requested.connect(lambda: manager.delete_selected(_op_items()))
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

    # ── Nav signals from MainWindow ─────────────────────────────
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
    # F312 — fill keyboard-only gaps
    QShortcut(QKeySequence("Alt+Return"), window).activated.connect(
        lambda: coord.toggle("info", manager.active_pane_id)
    )
    QShortcut(QKeySequence("Alt+B"), window).activated.connect(_open_bm_dialog)

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
    QShortcut(QKeySequence("Alt+Shift+N"),  window).activated.connect(_copy_names)

    def _set_permissions() -> None:
        if os.name != "posix":
            return
        from biome_fm.views.permissions_editor_dialog import PermissionsEditorDialog
        items = _op_items()
        if not items:
            return
        result = PermissionsEditorDialog.ask([i.path for i in items], window)
        if result is None:
            return
        mode, recursive = result
        manager.chmod_selected(items, mode, recursive)

    QShortcut(QKeySequence("Ctrl+Shift+P"), window).activated.connect(_set_permissions)

    # F408 — live zoom shortcuts
    def _zoom(delta: int) -> None:
        _apply_zoom(QApplication.instance(), cfg, cfg_dir / "config.toml", _system_pt, delta)

    QShortcut(QKeySequence("Ctrl+="), window).activated.connect(lambda: _zoom(+1))
    QShortcut(QKeySequence("Ctrl++"), window).activated.connect(lambda: _zoom(+1))
    QShortcut(QKeySequence("Ctrl+-"), window).activated.connect(lambda: _zoom(-1))
    QShortcut(QKeySequence("Ctrl+0"), window).activated.connect(lambda: _zoom(0))

    QShortcut(QKeySequence("F3"),           window).activated.connect(_toggle_preview_f3)

    def _open_in_editor_f4() -> None:
        item = _active().current_item()
        if item is not None and item.name != "..":
            open_in_editor(item.path, cfg.editor_cmd)

    QShortcut(QKeySequence("F4"),           window).activated.connect(_open_in_editor_f4)
    QShortcut(QKeySequence("F9"),           window).activated.connect(
        lambda: open_terminal(_active().current_path)
    )

    def _open_task_runner() -> None:
        from biome_fm.views.task_runner_dialog import TaskRunnerDialog
        dlg = TaskRunnerDialog(_active().current_path, window)
        dlg.exec()

    QShortcut(QKeySequence("Ctrl+Shift+M"), window).activated.connect(_open_task_runner)

    def _open_fullscreen() -> None:
        items = _active().active._items
        cursor = _active().current_item()
        idx = items.index(cursor) if cursor in items else 0
        dark = "dark" in cfg.theme.lower()
        viewer = FullscreenViewer(
            items, idx,
            lambda req: preview_registry.find(req.path).render(req),
            dark=dark, parent=window,
        )
        viewer.showMaximized()

    QShortcut(QKeySequence("F11"),          window).activated.connect(_open_fullscreen)

    def _open_shortcut_help() -> None:
        from biome_fm.views.shortcut_help_dialog import ShortcutHelpDialog
        ShortcutHelpDialog(window).exec()

    QShortcut(QKeySequence("?"),  window).activated.connect(_open_shortcut_help)
    QShortcut(QKeySequence("F1"), window).activated.connect(_open_shortcut_help)
    QShortcut(QKeySequence("Ctrl+Z"),       window).activated.connect(manager.undo)
    QShortcut(QKeySequence("Ctrl+Shift+Z"), window).activated.connect(manager.redo)
    QShortcut(QKeySequence("Ctrl+U"),       window).activated.connect(manager.swap_panes)
    QShortcut(QKeySequence("Ctrl+Shift+U"), window).activated.connect(manager.target_equals_source)
    QShortcut(QKeySequence("Ctrl+Shift+L"), window).activated.connect(manager.toggle_mirror)

    # ── Undo/Redo from menu ───────────────────────────────────────
    window.undo_requested.connect(manager.undo)
    window.redo_requested.connect(manager.redo)

    def _update_undo_redo_labels() -> None:
        undo_desc = history._undo_stack[-1].description if history._undo_stack else None
        redo_desc = history._redo_stack[-1].description if history._redo_stack else None
        window.update_undo_redo_labels(undo_desc, redo_desc)

    history.on_changed = _update_undo_redo_labels

    # ── Menu signals ─────────────────────────────────────────────
    window.refresh_requested.connect(lambda: _active().refresh())
    window.new_tab_requested.connect(_new_tab)
    window.close_tab_requested.connect(lambda: _active().close_tab(_active().active_idx))
    QShortcut(QKeySequence("Ctrl+R"), window).activated.connect(lambda: _active().refresh())

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

    def _apply_hidden_columns(names: list[str]) -> None:
        for tabs in (left_tabs, right_tabs):
            for v in tabs._views:
                v.set_hidden_columns(names)

    def _on_show_hidden(ev: ShowHiddenToggled) -> None:
        for proxy in _all_proxies():
            proxy.set_show_hidden(ev.enabled)
        save_config(cfg, cfg_dir / "config.toml")

    bus.subscribe(ShowHiddenToggled, _on_show_hidden)

    bus.subscribe(SyncBrowsingToggled,
                  lambda ev: [s.set_sync_indicator(ev.enabled) for s in (left_side, right_side)])

    if cfg.show_hidden:
        for proxy in _all_proxies():
            proxy.set_show_hidden(True)

    if cfg.hidden_columns:
        _apply_hidden_columns(cfg.hidden_columns)

    def _on_theme_changed(ev: ThemeChanged) -> None:
        for side in (left_side, right_side):
            side.style().unpolish(side)
            side.style().polish(side)
        dark = "dark" in ev.name.lower()
        # Update preview dark flag based on theme name
        preview_presenter.set_dark(dark)
        ai_panel._log.set_dark(dark)

    bus.subscribe(ThemeChanged, _on_theme_changed)

    # ── OS theme auto-switch ──────────────────────────────────────
    def _on_system_scheme_changed() -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QGuiApplication as _QGA

        from biome_fm.views.theme import apply_theme
        scheme = _QGA.styleHints().colorScheme()
        name = "dark" if scheme == Qt.ColorScheme.Dark else "light"
        apply_theme(QApplication.instance(), name, plugin_manager=plugins)

    from PySide6.QtGui import QGuiApplication
    _wire_system_theme(cfg, QGuiApplication.styleHints(), _on_system_scheme_changed)

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
        presenter = SettingsPresenter(
            cfg, dlg,
            available_themes=available_themes,
            available_plugins=plugin_names,
        )
        if dlg.exec():
            presenter.apply()
            if not cfg.show_git_status:
                for _t in [left_tabs, right_tabs]:
                    for _v in (_t.view_at(i) for i in range(_t.tab_count)):
                        _m = getattr(_v, "_model", None)
                        if _m and hasattr(_m, "set_git_status"):
                            _m.set_git_status({}, frozenset())
            from biome_fm.views.theme import apply_theme
            apply_theme(QApplication.instance(), cfg.theme, plugin_manager=plugins, glass=cfg.glass, glass_opacity=cfg.glass_opacity)
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
            if cfg.glass:
                from biome_fm.views.theme import _glass_alphas
                _, _sel = _glass_alphas(cfg.glass_opacity)
                preview_panel.set_code_alpha(_sel)
            else:
                preview_panel.set_code_alpha(255)
            bus.publish(ShowHiddenToggled(enabled=cfg.show_hidden))
            _apply_hidden_columns(cfg.hidden_columns)
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
        CommandEntry("Duplicate Tab",  "Ctrl+Alt+T",   _dup_tab),
        CommandEntry("Add to Collection",  "Ctrl+Alt+C", _collect_add),
        CommandEntry("Show Collection",    "Ctrl+Alt+V", _collect_show),
        CommandEntry("Close Tab",      "Ctrl+W",       lambda: _active().close_tab(_active().active_idx)),  # noqa: E501
        CommandEntry("Toggle AI",      "Ctrl+I",       lambda: coord.toggle("ai", manager.active_pane_id)),  # noqa: E501
        CommandEntry("Refresh",        "Ctrl+R",       lambda: _active().refresh()),
        CommandEntry("Copy Path",       "Ctrl+Shift+C", _copy_path),
        CommandEntry("Copy File Names", "Alt+Shift+N",  _copy_names),
        CommandEntry("Preview",        "F3",           _toggle_preview_f3),
        CommandEntry("Sync Browsing",  "Ctrl+Shift+L", manager.toggle_mirror),
        CommandEntry("Toggle Hidden",  "Ctrl+H",       manager.toggle_hidden),
        CommandEntry("Toggle Hidden",  "Ctrl+Shift+.", manager.toggle_hidden),
        CommandEntry("Back",           "Alt+Left",     lambda: _active().go_back()),
        CommandEntry("Forward",        "Alt+Right",    lambda: _active().go_forward()),
        CommandEntry("Up",             "Alt+Up",       lambda: _active().go_up()),
        CommandEntry("Home",           "Alt+Home",     lambda: _active().go_home()),
        CommandEntry("Settings",         "Ctrl+,",       _open_settings),
        CommandEntry("Find Files",       "Ctrl+Shift+F", sc.request_search),
        CommandEntry("Properties",       "Alt+Return",   lambda: coord.toggle("info", manager.active_pane_id)),
        CommandEntry("Bookmarks",        "Alt+B",        _open_bm_dialog),
    ]:
        registry.register(entry)

    cmd_store = CommandStore(cfg_dir / "commands.toml")
    for uc in cmd_store.commands:
        _uc_cmd = uc.command
        registry.register(CommandEntry(uc.label, uc.shortcut, lambda c=_uc_cmd: _run_cmd(c)))

    palette = CommandPalette(registry, parent=window)
    QShortcut(QKeySequence("Ctrl+P"), window).activated.connect(palette.open)

    # ── Fuzzy file finder ─────────────────────────────────────────
    fuzzy = FuzzyFinder(parent=window)
    def _on_fuzzy_chosen(path: Path) -> None:
        _active().navigate_to(path if path.is_dir() else path.parent)
        if path.is_file() and hasattr(v := _active().view_at(_active().active_idx), "select_item"):
            v.select_item(path.name)

    QShortcut(QKeySequence("Ctrl+Shift+P"), window).activated.connect(
        lambda: fuzzy.open(_active().current_path)
    )
    fuzzy.file_chosen.connect(_on_fuzzy_chosen)

    def _apply_highlight_rules(rules: list[dict]) -> None:
        hr = [HighlightRule(d["pattern"], d["color"]) for d in rules]
        for _t in (left_tabs, right_tabs):
            for _v in (_t.view_at(i) for i in range(_t.tab_count)):
                _m = getattr(_v, "_model", None)
                if _m and hasattr(_m, "set_highlight_rules"):
                    _m.set_highlight_rules(hr)

    def _open_highlight_rules() -> None:
        result = HighlightRulesDialog.get_rules(cfg.highlight_rules, window)
        if result is not None:
            cfg.highlight_rules = result
            save_config(cfg, cfg_dir / "config.toml")
            _apply_highlight_rules(result)

    window.highlight_rules_requested.connect(_open_highlight_rules)
    if cfg.highlight_rules:
        _apply_highlight_rules(cfg.highlight_rules)

    QShortcut(QKeySequence("Ctrl+,"), window).activated.connect(_open_settings)
    window.settings_requested.connect(_open_settings)
    window.workspaces_requested.connect(_open_workspace_dialog)

    def _open_dup_finder() -> None:
        from biome_fm.views.duplicate_panel import DuplicateFinderDialog
        root = _active().current_path
        dlg = DuplicateFinderDialog(root, parent=window)

        def _delete(paths: list) -> None:
            for p in paths:
                try:
                    Path(p).unlink()
                except OSError:
                    pass
            _active().refresh()

        dlg.delete_requested.connect(_delete)
        dlg.show()

    window.find_duplicates_requested.connect(_open_dup_finder)
    QShortcut(QKeySequence("Ctrl+Shift+D"), window).activated.connect(_open_dup_finder)

    def _open_storage_treemap() -> None:
        from biome_fm.views.treemap_panel import TreemapPanel
        panel = TreemapPanel(parent=window)
        panel.scan(_active().current_path)
        panel.show()

    QShortcut(QKeySequence("Ctrl+Shift+T"), window).activated.connect(_open_storage_treemap)

    def _open_large_file_finder() -> None:
        from biome_fm.views.large_file_dialog import LargeFileDialog
        dlg = LargeFileDialog(_active().current_path, parent=window)
        dlg.navigate_requested.connect(lambda p: _active().navigate_to(p.parent))
        dlg.show()

    QShortcut(QKeySequence("Ctrl+Shift+L"), window).activated.connect(_open_large_file_finder)

    def _open_panelize() -> None:
        from biome_fm.utils.panelize import parse_shell_output
        cmd, ok = QInputDialog.getText(window, "Panelize", "Shell command:")
        if not ok or not cmd.strip():
            return
        import subprocess as _sp
        try:
            proc = _sp.run(
                cmd, shell=True, capture_output=True, text=True,
                cwd=str(_active().current_path), timeout=30,
            )
            items = parse_shell_output(proc.stdout, _active().current_path)
        except Exception:
            items = []
        if items:
            _active().navigate_virtual(items, label=f"$ {cmd}")

    window.panelize_requested.connect(_open_panelize)

    def _open_cloud_profiles() -> None:
        from biome_fm.models.cloud_profile_store import CloudProfileStore
        from biome_fm.views.cloud_profile_dialog import CloudProfileDialog
        _store = CloudProfileStore(cfg_dir / "cloud_profiles.toml")
        _store.load()
        dlg = CloudProfileDialog(_store, parent=window)
        dlg.exec()

    window.cloud_profiles_requested.connect(_open_cloud_profiles)

    # ── Quick-connect bar ─────────────────────────────────────────
    from biome_fm.models.cloud_profile_store import CloudProfileStore as _CPS
    from biome_fm.models.ssh_profiles import SSHProfileStore as _SPS
    from biome_fm.views.quick_connect_bar import QuickConnectBar as _QCBar
    _ssh_store = _SPS(cfg_dir / "ssh_profiles.toml")
    _ssh_store.load()
    _cloud_store2 = _CPS(cfg_dir / "cloud_profiles.toml")
    _cloud_store2.load()
    _qcbar = _QCBar(window)
    _qc_profiles: list[tuple[str, str]] = []
    for _sp in _ssh_store.list_all():
        _port = f":{_sp.port}" if _sp.port != 22 else ""
        _user = f"{_sp.user}@" if _sp.user else ""
        _qc_profiles.append((_sp.name, f"sftp://{_user}{_sp.host}{_port}/"))
    for _cp in _cloud_store2.list_all():
        _root = f"{_cp.host}/{_cp.bucket}" if _cp.bucket else _cp.host
        _qc_profiles.append((_cp.name, f"{_cp.scheme}://{_root}/"))
    _qcbar.set_profiles(_qc_profiles)
    _qcbar.connect_requested.connect(lambda uri: manager.navigate_active(Path(uri)))
    window.statusBar().addWidget(_qcbar)

    def _open_temp_panel() -> None:
        from biome_fm.views.temp_panel import TempPanel
        dlg = TempPanel(parent=window)
        dlg.show()

    window.temp_panel_requested.connect(_open_temp_panel)

    def _open_sync_dialog() -> None:
        from biome_fm.presenters.compare_presenter import ComparePresenter
        from biome_fm.presenters.sync_presenter import preview_sync
        from biome_fm.views.sync_dialog import SyncDialog
        try:
            left_items = vfs.listdir(left_tabs.current_path)
            right_items = vfs.listdir(right_tabs.current_path)
        except OSError:
            return
        entries = ComparePresenter(left_items, right_items).compare()
        dlg = SyncDialog(entries, left_tabs.current_path, right_tabs.current_path, parent=window)

        def _on_sync(checked_entries, direction, mirror: bool = False) -> None:
            ops = preview_sync(
                checked_entries, direction,
                left_tabs.current_path, right_tabs.current_path,
                mirror=mirror,
            )
            for op in ops:
                try:
                    if op.action == "delete_orphan":
                        vfs.delete(op.src)
                    else:
                        vfs.copy(op.src, op.dst / op.src.name)
                except OSError:
                    pass
            manager._refresh_both()

        dlg.sync_requested.connect(_on_sync)
        dlg.show()

    window.sync_dirs_requested.connect(_open_sync_dialog)

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
        cfg.splitter_sizes = coord.pane_sizes()
        _close_field = _AI_MODEL_FIELDS.get(ai_presenter._active_key)
        if _close_field:
            setattr(cfg, _close_field, ai_presenter._provider.active_model)
        save_config(cfg, cfg_dir / "config.toml")
        ai_presenter.shutdown()
        drain_timer.stop()
        preview_presenter.shutdown()
        preview_timer.stop()
        size_drain_timer.stop()
        search_timer.stop()
        op_timer.stop()
        refresh_timer.stop()
        watch_timer.stop()
        left_watcher.stop()
        right_watcher.stop()
        op_queue.shutdown(wait=False)

    # ── Leader key (which-key popup, F290) ───────────────────────
    from biome_fm.presenters.leader_handler import LeaderHandler
    from biome_fm.views.leader_filter import LeaderFilter
    from biome_fm.views.which_key_popup import WhichKeyPopup

    _leader = LeaderHandler()
    _leader.register("\\r", lambda: _active().refresh())
    _leader.register("\\h", manager.toggle_hidden)
    _leader.register("\\t", _dup_tab)
    _leader.register("\\p", palette.open)
    _leader.register("\\s", sc.request_search)
    _wk_popup = WhichKeyPopup(window)
    _wk_filter = LeaderFilter(_leader, _wk_popup)
    QApplication.instance().installEventFilter(_wk_filter)  # type: ignore[union-attr]

    def _guard_close() -> bool:
        """F268: ask before quitting while ops are running."""
        if op_queue.active_count() == 0:
            return True
        reply = QMessageBox.question(
            window,
            "Operations Running",
            "Operations are still running. Quit anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    window._close_guard = _guard_close  # type: ignore[attr-defined]
    window.about_to_close.connect(_on_close)
    window._ctx = _AppContext(  # type: ignore[attr-defined]
        manager=manager,
        left_tabs=left_tabs,
        right_tabs=right_tabs,
        ai_presenter=ai_presenter,
        preview_presenter=preview_presenter,
        info_presenter=info_presenter,
        coord=coord,
        panel_mgr=panel_mgr,
        op_queue=op_queue,
        plugins=plugins,
        git_worker=git_worker,
        timers=[drain_timer, preview_timer, size_drain_timer, op_timer, search_timer, refresh_timer, watch_timer],
        tray=_tray,
        hotkey_listener=_hotkey_listener,
    )

    return window
