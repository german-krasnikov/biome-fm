# Biome FM Architecture

## Overview

```
src/biome_fm/
├── __main__.py         # CLI entry point: dispatches known subcommands (configure/doctor/version/uninstall/mcp)
│                       #   via mcp/cli.dispatch() before importing Qt; falls through to QApplication bootstrap
├── app.py              # create_app() factory — full DI wiring (VFSRouter, Config,
│                       #   Session, Plugins, AI, CommandPalette, PaneSideViews);
│                       #   nav/DnD/context-menu signal wiring; focus tracking → active pane bus;
│                       #   toolbar signals (refresh/new_tab); _copy_path/_quick_look/_reveal_in_finder
│                       #   closures; Ctrl+Z/Ctrl+Shift+Z/F3/Ctrl+Shift+C/Ctrl+Shift+L shortcuts;
│                       #   _wire_pane() / _wire_ctx() / _new_tab() helpers
├── qt.py               # Centralised PySide6 imports (Anki pattern); includes QMimeData, QDrag
├── config.py           # @dataclass Config + TOML loader (save_config / load_config)
├── session.py          # SessionState / PaneSideState / TabState / PanelSession → JSON persistence;
│                       #   PanelSession.overlay_side persists which pane the panel occupies
├── panel_manager.py    # Pure-Python state machine (no Qt); states: HIDDEN / OVERLAY / FLOATING;
│                       #   Effect dataclass (kind, target_side); kind values:
│                       #   show_overlay, show_floating, hide, focus_floating, set_opposite_visible;
│                       #   PanelManager.toggle(name, active_side) → list[Effect]
├── event_bus.py        # Decoupled pub/sub (EventBus singleton);
│                       #   events: FilesChanged, ActivePaneChanged, OperationStarted,
│                       #   OperationFinished, PaneNavigated, SyncBrowsingToggled,
│                       #   BookmarkChanged, ThemeChanged(name, tokens),
│                       #   ShowHiddenToggled(enabled: bool),
│                       #   AsyncOpSubmitted(task_id, description, cancel)
│
├── models/
│   ├── file_item.py        # FileItem frozen dataclass (slots=True); size_str property
│   ├── vfs.py              # VFSProtocol + LocalVFS
│   ├── vfs_router.py       # VFSRouter: path ancestry walk → archive root detection;
│   │                       #   dispatches local/archive; caches ArchiveVFS per archive file
│   ├── archive_vfs.py      # ZIP/TAR.GZ VFS via fsspec
│   ├── directory_model.py  # QAbstractTableModel (4 cols: Name/Size/Modified/Ext);
│   │                       #   flags() adds ItemIsDragEnabled (DnD root-cause fix);
│   │                       #   ForegroundRole: file-type coloring via _EXT_COLORS dict
│   │                       #   (archives=orange, images=pink, code=green, docs=blue, media=yellow);
│   │                       #   hidden files dimmed (#565F89); ToolTipRole = path + modified + size;
│   │                       #   DirSortFilterProxy: '..' pinned first, dirs before files,
│   │                       #   set_filter(text) for Quick Filter,
│   │                       #   set_show_hidden(bool) hides dotfiles when False
│   ├── bookmark_store.py   # TOML-backed list[Path]; add/remove/all/__contains__;
│   │                       #   reads/writes [bookmarks] paths = [...] via tomllib
│   ├── icon_provider.py    # icon_for_extension(ext) — @lru_cache(256), QFileIconProvider;
│   │                       #   icon_for_dir() — SP_DirIcon; fallback to SP_FileIcon
│   └── markdown_renderer.py # render(md, dark) → HTML for QTextBrowser.setHtml();
│                            #   QTextDocument.setMarkdown(GFM) → toHtml(); Pygments replaces
│                            #   <pre> blocks with highlighted HTML (monokai dark / default light);
│                            #   dark/light-aware CSS injected into <head>; PRE_GROUP_RE regex fixed
│                            #   (no `+` grouping); @lru_cache(maxsize=2) on HtmlFormatter;
│                            #   100KB truncation limit; must run on Qt main thread
│
├── presenters/
│   ├── pane_presenter.py     # Drives one pane (cd, select, sort, current_item);
│   │                         #   PaneViewProtocol: set_items/set_path/show_error/set_status/
│   │                         #   set_marked/current_cursor_item/advance_cursor/retreat_cursor/
│   │                         #   set_filter_visible/select_item;
│   │                         #   back/forward stacks; archive in-pane via _is_archive()
│   │                         #   (_ARCHIVE_SUFFIXES: .zip/.tar/.tar.gz/.tar.bz2/.tgz; .7z excluded);
│   │                         #   go_up() calls select_item(prev_name) so cursor lands on the
│   │                         #   folder the user came from (classic FM UX);
│   │                         #   _update_status: marks + free-space (cached disk_usage); _fmt_size;
│   │                         #   selection ops: toggle_mark/toggle_mark_up/select_all/
│   │                         #   deselect_all/invert_selection/select_by_pattern/deselect_by_pattern
│   ├── tabs_presenter.py     # Owns N PanePresenters per side; duck-types as PanePresenter
│   │                         #   for ManagerPresenter; TabsViewProtocol requires set_tab_tooltip;
│   │                         #   tabs display abbreviated path (~/... or …/name if >30 chars);
│   │                         #   tooltip = full str(path); opener param passed to each PanePresenter
│   ├── manager_presenter.py  # Inter-pane ops (copy, move, delete, mkdir, rename);
│   │                         #   drop_files(paths, target_pane_id, move, target_folder) — DnD;
│   │                         #   async path: ProgressCopyCmd/ProgressMoveCmd submitted to OpQueue,
│   │                         #   publishes AsyncOpSubmitted(task_id, desc, cancel);
│   │                         #   toggle_mirror() / navigate_active() for Sync Browsing;
│   │                         #   toggle_hidden() — flips Config.show_hidden, publishes ShowHiddenToggled;
│   │                         #   undo/redo via CommandHistory → refresh_both()
│   ├── ai_presenter.py       # AI chat bridge (AIProvider ↔ AIChatViewProtocol)
│   ├── compare_presenter.py  # Directory diff (left vs right pane)
│   ├── rename_presenter.py   # Multi-rename (pattern, counter, ext substitution)
│   ├── search_presenter.py   # File search (name glob + content grep)
│   └── settings_presenter.py # SettingsPresenter (no Qt) + SettingsViewProtocol;
│                               #   load/save Config fields via protocol methods;
│                               #   tabs: General, Appearance, AI, Plugins
│
├── views/
│   ├── main_window.py    # QMainWindow: splitter, AI panel toggle (checkable QAction in toolbar),
│   │                     #   closeEvent, splitter_sizes persistence, _build_menubar, _build_toolbar;
│   │                     #   command line visible by default; _on_cmd executes shell command
│   │                     #   with cwd=active pane path, emits command_submitted signal;
│   │                     #   _HistoryLineEdit (30-item dedup history, Up/Down nav) +
│   │                     #   case-insensitive QCompleter (dropdown history);
│   │                     #   signals: back/forward/up/home + undo/redo/refresh/new_tab _requested,
│   │                     #   command_submitted, about_to_close; tab_shortcut (Tab key QShortcut)
│   ├── pane_side_view.py # _PathTabBar (Ctrl+click / middle-click copies full path from tooltip);
│   │                     #   tabs movable; _sync_closable() — close buttons only when >1 tab;
│   │                     #   set_tab_title() sets abbreviated display + full tooltip;
│   │                     #   set_tab_tooltip(); set_active() toggles QSS dynamic property
│   ├── pane_view.py      # QWidget: nav buttons (←→↑⌂ with tooltips) + path bar + table + bars;
│   │                     #   _PaneTableView (inner QTableView subclass): full DnD impl
│   │                     #   (mimeData/startDrag/dragEnterEvent/dragMoveEvent/dropEvent);
│   │                     #   MIME type application/x-biome-fm-paths; Shift-drop = move;
│   │                     #   key routing: Enter/Return=item_activated, Space/F3=PreviewPanel toggle,
│   │                     #   Shift+Down=mark, Shift+Up=mark_up, /=FilterBar, printable→JumpBar;
│   │                     #   context menu: Copy/Move/Delete/Rename/Copy Path/Preview/Open in Finder
│   │                     #   (platform label); setUniformRowHeights() compat stub; table: no grid,
│   │                     #   alternatingRowColors, 22px rows, vertical header hidden;
│   │                     #   Name=Stretch, Size/Modified/Ext=Interactive;
│   │                     #   retreat_cursor() for Shift+Up mark; advance_cursor() for mark;
│   │                     #   select_item(name) scrolls to and selects row by filename;
│   │                     #   _DropHintDelegate: QStyledItemDelegate draws 2px highlight border
│   │                     #   around folder row when _drop_hint_row matches; _drop_hint_row
│   │                     #   set in dragMoveEvent (folder under cursor) / cleared on dragLeave;
│   │                     #   drop on folder → emits target_folder path; drop on blank → None;
│   │                     #   10 signals: item_activated, path_change_requested,
│   │                     #   mark_toggle_requested, mark_toggle_up_requested, view_requested,
│   │                     #   back/forward/up/home_requested, context_action_requested;
│   │                     #   files_dropped = Signal(list, bool, object)
│   │                     #     → (paths: list[Path], move: bool, target_folder: Path | None)
│   ├── filter_bar.py     # FilterBar: QLineEdit-based quick filter; hidden by default;
│   │                     #   activate() shows + focuses; Escape → deactivate + closed signal;
│   │                     #   filter_changed(str) signal → DirSortFilterProxy.set_filter()
│   ├── jump_bar.py       # JumpBar: type-to-navigate overlay label; append_char() accumulates
│   │                     #   keystrokes, emits jump_text_changed(str); auto-clears after 600ms;
│   │                     #   PaneView._on_jump() scans proxy rows for prefix match
│   ├── ai_chat_panel.py  # Passive AI chat (message_submitted Signal)
│   ├── action_bar.py     # F1-F10 function key bar (tooltips on all buttons)
│   ├── command_palette.py # Fuzzy-search command launcher (Ctrl+P)
│   ├── preview_panel.py  # PreviewPanel (QWidget): QStackedWidget with 3 widgets
│   │                     #   (busy label, image QLabel, QTextBrowser); animated slide on
│   │                     #   maximumWidth (150ms OutCubic); DEFAULT_WIDTH=350;
│   │                     #   visibility_changed(bool) signal; implements PreviewViewProtocol
│   ├── panel_coordinator.py  # QObject: dispatches Effect → Qt widget ops;
│   │                         #   accepts left_side + right_side PaneSideView widgets;
│   │                         #   toggle(name, active_side="left") opens panel in the
│   │                         #   OPPOSITE pane (active left → right; active right → left);
│   │                         #   _saved_sizes keyed by widget; _hidden_widget tracks displaced pane;
│   │                         #   detach() creates floating QDialog; save_state/restore_state
│   │                         #   round-trips overlay_side to PanelSession
│   ├── breadcrumb_bar.py # BreadcrumbBar: QStackedWidget (breadcrumb ↔ edit modes);
│   │                      #   breadcrumb mode = _CrumbRow with _SegmentButton per path segment;
│   │                      #   edit mode = inline _PathComboBox; click segment → navigate;
│   │                      #   RMB context: Copy Path / Copy Name / Show in Finder / Open Terminal Here;
│   │                      #   horizontal wheel/swipe → back/forward (threshold 120, 300ms cooldown);
│   │                      #   signals: path_entered(str), back_requested, forward_requested;
│   │                      #   path_segments(path) → list[(label, Path)] pure helper (no Qt)
│   ├── settings_dialog.py # QDialog (4 tabs: General/Appearance/AI/Plugins);
│   │                      #   passive view implementing SettingsViewProtocol;
│   │                      #   General: show_hidden QCheckBox, sync_browsing QCheckBox;
│   │                      #   Appearance: theme QComboBox, file_type_colors QCheckBox;
│   │                      #   AI: provider QComboBox, API key QLineEdits, Ollama URL/model;
│   │                      #   Plugins: read-only QListWidget of installed plugins
│   ├── progress_dialog.py # Modeless QDialog for async file ops; shows file label,
│   │                      #   bytes QProgressBar, overall label, files QProgressBar, Cancel button;
│   │                      #   update(files_done, files_total, bytes_done, bytes_total, name);
│   │                      #   Cancel button sets threading.Event; auto-closes on OpDone/OpCancelled
│   └── theme.py          # TOML-based theme system; load_theme(name) resolves plugin hook
│                          #   → TOML inheritance (meta.inherits) → _DARK_FALLBACK;
│                          #   _find_theme(): user AppConfig/biome-fm/themes/ first, then
│                          #   importlib.resources; _apply_palette() maps 10 tokens to QPalette;
│                          #   apply_theme(app, name, plugin_manager) publishes ThemeChanged;
│                          #   _TOKENS alias kept for backward compat; Template(_QSS_TMPL) fills QSS
│
├── commands/
│   ├── base.py           # Command ABC (execute/undo/undoable) + CommandHistory (50 levels);
│   │                     #   CommandHistory.push(cmd) records already-executed cmd for undo
│   ├── registry.py       # CommandRegistry + CommandEntry (id, name, shortcut, fn)
│   ├── copy_cmd.py       # CopyCmd (shutil.copy2);
│   │                     #   ProgressCopyCmd: 256KB-chunk copy with cancel (threading.Event)
│   │                     #   + report(files_done, files_total, bytes_done, bytes_total, name);
│   │                     #   raises Cancelled on cancel.is_set(); undo deletes created files
│   ├── move_cmd.py       # MoveCmd;
│   │                     #   ProgressMoveCmd: same cancel + report API, wraps shutil.move
│   ├── delete_cmd.py     # DeleteCmd (send2trash)
│   ├── rename_cmd.py     # RenameCmd
│   ├── mkdir_cmd.py      # MkdirCmd
│   └── multi_rename_cmd.py # MultiRenameCmd (batch with pattern/counter)
│
├── operations/
│   ├── queue.py          # OpQueue: asyncio + ThreadPoolExecutor;
│   │                     #   submit(cmd, cancel, task_id) — accepts external cancel Event;
│   │                     #   next_task_id() / put_event() for async path in ManagerPresenter;
│   │                     #   _run() catches Cancelled → emits OpCancelled
│   └── task.py           # OpTask: priority, cancel (threading.Event), progress callback;
│                         #   Cancelled exception (raised inside Command to signal cancellation);
│                         #   OpStarted, OpProgress(task_id, files_done, files_total,
│                         #     bytes_done, bytes_total, current_file),
│                         #   OpDone, OpError, OpCancelled;
│                         #   OpEvent = union of all above
│
├── preview/
│   ├── provider.py       # PreviewProvider Protocol (priority, can_handle, render);
│   │                     #   ContentKind enum (IMAGE/TEXT/HTML/MARKDOWN/ERROR);
│   │                     #   PreviewRequest(path, dark); PreviewResult(kind, data, title)
│   ├── registry.py       # PreviewRegistry: sorted list[PreviewProvider] by priority;
│   │                     #   find(path) → first match or FallbackProvider()
│   ├── presenter.py      # PreviewPresenter (Qt-free): ThreadPoolExecutor(max_workers=1);
│   │                     #   64-item LRU cache keyed (path, mtime, dark); queue.SimpleQueue for
│   │                     #   thread→main delivery; drain() polled by QTimer;
│   │                     #   toggle_item(), update_if_visible(), set_dark(), shutdown()
│   └── providers/
│       ├── image.py      # ImagePreviewProvider (priority=0); jpg/png/gif/webp/svg etc; 50MB limit
│       ├── markdown.py   # MarkdownPreviewProvider (priority=5); .md/.markdown/.mdx; 200KB limit;
│       │                 #   calls markdown_renderer.render(md, dark) → HTML;
│       │                 #   rendering runs on main thread (Qt requirement); returns ContentKind.HTML
│       ├── code.py       # CodePreviewProvider (priority=8); Pygments syntax highlighting;
│       │                 #   get_lexer_for_filename() to detect language; skips TextLexer (falls
│       │                 #   through to TextPreviewProvider); monokai dark / friendly light;
│       │                 #   @lru_cache(maxsize=2) HtmlFormatter; 512KB limit; ContentKind.HTML
│       ├── text.py       # TextPreviewProvider (priority=10); .py/.js/.toml/.json etc; 256KB limit
│       └── fallback.py   # FallbackProvider (priority=999); always handles; returns HTML metadata
│
├── themes/
│   ├── _base.qss.tmpl    # string.Template QSS; uses $base $surface $accent etc (10 tokens)
│   ├── dark.toml         # [meta] name=Dark; [tokens] 10 macOS system-color values
│   ├── light.toml        # [meta] name=Light; [tokens] 10 light-mode values
│   └── catppuccin-mocha.toml  # third-party palette example
│
├── plugins/
│   ├── types.py          # ThemeTokens (TypedDict, 10 keys); ActionSpec dataclass
│   │                     #   (label, callback, shortcut, icon_name, separator_before);
│   │                     #   ColumnDef dataclass (id, title, width, alignment)
│   ├── hookspecs.py      # pluggy @hookspec: register_commands (historic=True),
│   │                     #   on_navigate(path), on_file_operation(op,src,dst),
│   │                     #   provide_theme(name) firstresult → ThemeTokens | None,
│   │                     #   before_file_operation(op,src,dst) firstresult → bool | None,
│   │                     #   context_menu_actions(items,pane_id) → list[ActionSpec],
│   │                     #   extra_columns() → list[ColumnDef],
│   │                     #   extra_archive_extensions() → list[str]
│   ├── manager.py        # PluginManager: API_VERSION=(1,0); register_plugin() checks
│   │                     #   BIOME_FM_API_VERSION major; load_entry_points() via
│   │                     #   importlib.metadata group='biome_fm.plugins';
│   │                     #   load_local_plugins(plugin_dir) loads .py files + dirs with
│   │                     #   __init__.py from ~/.config/biome-fm/plugins/, each must have
│   │                     #   top-level Plugin class; get_installed_plugins() → list[dict]
│   ├── theme_registry.py # ThemeRegistry(pm): resolve(name) → _DARK_FALLBACK merged with
│   │                     #   plugin hook result (provide_theme firstresult)
│   └── builtin/
│       ├── __init__.py
│       └── dark_theme.py # BuiltinDarkTheme: BIOME_FM_API_VERSION=(1,0);
│                         #   provide_theme("dark") → _DARK_FALLBACK copy; None for other names
│
├── ai/
│   ├── __init__.py       # Package init
│   ├── provider.py       # AIProviderProtocol (runtime-checkable) + NoOpProvider +
│   │                     #   make_providers(cfg) → dict[str, AIProviderProtocol];
│   │                     #   includes make_cli_providers() via ai/cli/backend_def
│   ├── claude_provider.py # ClaudeProvider (anthropic SDK, chat + chat_stream)
│   ├── openai_provider.py # OpenAIProvider (openai SDK, chat + chat_stream)
│   ├── ollama_provider.py # OllamaProvider (HTTP API, chat + chat_stream)
│   ├── types.py          # FileContent, ImageContent dataclasses for attachments
│   └── cli/              # CLI-tool AI providers (subprocess.Popen, no SDK dependency)
│       ├── backend_def.py # BackendDef frozen dataclass (name, cmd, models, prompt_fmt);
│       │                  #   CLAUDE_CODE / CODEX / OPENCODE constants;
│       │                  #   make_cli_providers() → dict keyed by name, only found binaries
│       ├── cli_provider.py # CliProvider: AIProviderProtocol via Popen; chat/chat_stream;
│       │                  #   resolve_binary() → Path | None; generator.close() → proc.terminate()
│       └── stream_parse.py # Line normalizers: parse_claude_code_line / parse_codex_line /
│                           #   parse_plain_line → str | None (skip control/JSON lines)
│
├── mcp/                  # MCP server + CLI installer (no Qt dependency)
│   ├── server.py         # create_server(allowed_roots) → FastMCP("biome-fm");
│   │                     #   registers fs_read + fs_write tool modules;
│   │                     #   _validate_path() blocks traversal outside allowed_roots
│   ├── _entry.py         # biome-fm-mcp entry point: create_server().run() stdio transport
│   ├── cli.py            # dispatch(argv) → int | UNHANDLED; subcommands:
│   │                     #   configure (auto/--client KEY), doctor, version, uninstall, mcp;
│   │                     #   UNHANDLED sentinel object for __main__ fallthrough
│   ├── clients.py        # ClientInfo(name, config_path, fmt); CLIENT_REGISTRY dict (8 clients:
│   │                     #   claude-code, claude-desktop, cursor, windsurf, vscode,
│   │                     #   opencode, codex, kimi); detect_installed() → list[str]
│   ├── merger.py         # merge_mcp_config/remove_mcp_entry for JSON clients;
│   │                     #   merge_toml_mcp/remove_toml_mcp_entry for TOML clients;
│   │                     #   atomic writes via temp file + rename
│   ├── resolver.py       # find_server_command() → list[str] (uvx > venv > python -m);
│   │                     #   build_server_entry() → dict ready for client config injection
│   └── tools/
│       ├── __init__.py   # _validate_path(path_str, allowed_roots) → Path (traversal guard)
│       ├── fs_read.py    # register(mcp, vfs, allowed_roots): 4 tools —
│       │                 #   list_directory, stat_item, read_file (64KB cap), search_files
│       └── fs_write.py   # register(mcp, vfs, history, allowed_roots): 6 tools —
│                         #   copy_files, move_files, delete_files, make_directory,
│                         #   rename_file, undo_last — all via Command pattern + CommandHistory
│
└── utils/
    ├── platform.py       # IS_MAC / IS_WIN / IS_LINUX; quick_look(path), quick_look_item(item),
    │                     #   reveal_in_finder(path), get_modifier_name() — cross-platform
    │                     #   (macOS: qlmanage -p / open -R; Windows: explorer /select; Linux: xdg-open)
    └── opener.py         # open_file(path) — default app opener (macOS: open, Win: os.startfile,
                          #   Linux: xdg-open); guards against virtual archive paths (path.exists()
                          #   check → set_status instead of show_error); passed to TabsPresenter as opener=
```

## Patterns

### Hybrid Supervising Controller (MVP variant)
Views emit signals → Presenters react → update Models → push state to Views.
Views NEVER import models. Presenters have ZERO Qt imports — testable with plain Python mocks.
Model is a thin data adapter (QAbstractTableModel wrapping list[FileItem]).

### Command + Undo
Every file mutation = Command(execute + undo). CommandHistory (50 levels).
CommandRegistry maps string ids to callables for CommandPalette dispatch.
ManagerPresenter wires undo/redo to CommandHistory + refresh_both().

### VFS Host Chaining
VFSRouter walks path ancestry to detect archive roots (`.zip`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tgz`). `.7z` is explicitly excluded — unsupported by fsspec backend.
Matching paths → ArchiveVFS (fsspec); plain paths → LocalVFS.
Nested archives supported via chained VFS instances; ArchiveVFS instances cached per root file.
`PanePresenter._is_archive()` triggers in-pane browsing on item activation.

### Plugin Hooks (pluggy)
Hookspecs: `register_commands` (historic), `on_navigate`, `on_file_operation`,
`before_file_operation`, `provide_theme` (firstresult), `context_menu_actions`,
`extra_columns`, `extra_archive_extensions`.
Discovery: `importlib.metadata.entry_points(group="biome_fm.plugins")` + local
`~/.config/biome-fm/plugins/` scan. API versioning gates plugins on major version mismatch.
Builtin plugins live in `plugins/builtin/` and are registered in `create_app()`.

### Multi-Tab Panes
Each side (left/right) has a PaneSideView (QTabBar + QStackedWidget) driven by a TabsPresenter
owning N PanePresenters. Tabs persist to session.json via SessionState.
`_PathTabBar` (QTabBar subclass): middle-click or Ctrl+click copies full path from tooltip.
`_sync_closable()` shows close buttons only when tab count > 1.

### AI Integration (Multi-Model)
`AIProviderProtocol` with `chat()` and `chat_stream()` methods. Three providers:
`ClaudeProvider`, `OpenAIProvider`, `OllamaProvider`. `make_providers(cfg)` builds
available providers from config/env at startup; `NoOpProvider` fallback if none configured.
`AIChatPanel` composed of `ChatLog` (bubble-style HTML with streaming), `ContextBar`
(DnD file attachment chips), and model selector `QComboBox`. `AIPresenter` manages
active provider + model; streams tokens via `queue.SimpleQueue` → `QTimer` drain.
A 100ms QTimer drains the AI stream in `app.py`.

### Drag and Drop
`_PaneTableView` (inner class in pane_view.py) subclasses QTableView to override
`mimeData`/`startDrag`/`dragEnterEvent`/`dragMoveEvent`/`dragLeaveEvent`/`dropEvent`.
MIME type: `application/x-biome-fm-paths` (newline-joined absolute paths).
Folder highlight: `_DropHintDelegate` paints a 2px accent-colored rect around the row
stored in `_drop_hint_row`; `dragMoveEvent` sets it to the row under cursor if that
row is a non-`..` directory, or -1 otherwise; `dragLeaveEvent` clears it.
Drops emit `files_dropped(paths: list[Path], move: bool, target_folder: Path | None)`
on `PaneView`. `target_folder` is the hovered folder's path if dropping on a folder,
else None (drop goes to pane's current directory).
`app.py` wires this to `ManagerPresenter.drop_files(paths, target_pane_id, move, target_folder)`,
which resolves paths, filters same-dir no-ops, then dispatches ProgressCopyCmd or ProgressMoveCmd
via OpQueue (async path). `DirectoryModel.flags()` adds `ItemIsDragEnabled`.

### Active Pane Tracking
`app.py` tracks focus via `focusChanged` (QApplication signal).
The active `PaneSideView` receives `set_active(True)`, the inactive one `False`.
`set_active()` toggles QSS dynamic property `active`; `_base.qss.tmpl` applies a
3px left accent border + 1px top accent border (transparent borders of same width
for inactive pane to prevent layout shift).
`ManagerPresenter.set_active_pane(pane_id)` keeps the presenter layer in sync for
operations that target the opposite pane.
`ActivePaneChanged` event is published to the EventBus on every switch.

### Nav Bar
`PaneView` renders a row of icon nav buttons (←back, →forward, ↑up, ⌂home) above the
table. Each button is connected to a dedicated Signal; `PanePresenter` handles them
via the same `PaneViewProtocol` interface, keeping the view passive.
Buttons use `QStyle.StandardPixmap` icons and have keyboard shortcut tooltips.

### Quick Filter
`/` key in `_PaneTableView` calls `parent.filter_bar.activate()`.
`FilterBar` is a hidden QLineEdit row in PaneView; `filter_changed` → `DirSortFilterProxy.set_filter()`.
Escape deactivates and clears the filter.

### Type-to-Navigate (JumpBar)
Any printable keystroke (not Ctrl/Alt modified, not Space) routes to `JumpBar.append_char()`.
`JumpBar` shows an overlay label with accumulated text, emits `jump_text_changed`.
`PaneView._on_jump()` scans proxy rows for the first name with matching prefix (case-insensitive).
Auto-clears after 600ms of inactivity.

### File-Type Coloring
`DirectoryModel.data(ForegroundRole)` returns a colored `QBrush` per extension group:
archives=orange, images=pink, code/scripts=green, docs=blue, media=yellow.
Hidden files (starting with `.`) are dimmed. Directories and `..` are unstyled.

### Sync Browsing
`ManagerPresenter.toggle_mirror()` toggles `_mirror` flag.
`navigate_active(path)` navigates the active pane; if mirror is on, also navigates the opposite pane.
Re-entrancy guard `_mirroring` prevents infinite loops.
Wired to `Ctrl+Shift+L` shortcut in `app.py`.

### Theme / Skins (v0.7.0)

Themes are TOML files with 10 named color tokens. A `string.Template` in
`themes/_base.qss.tmpl` is substituted at apply time to produce the full QSS.

`ThemeTokens` TypedDict keys (all 10): `base`, `surface`, `surface2`, `border`,
`text`, `text_dim`, `accent`, `accent2`, `red`, `green`.

```
apply_theme(app, name, plugin_manager)
      │
      ├─ plugin_manager.hook.provide_theme(name)  [firstresult]
      │        result merged over _DARK_FALLBACK
      │
      ├─ _find_theme(name):
      │        1. ~/.config/biome-fm/themes/<name>.toml      (user override)
      │        2. ~/.config/biome-fm/themes/<name>/theme.toml
      │        3. importlib.resources biome_fm.themes/<name>.toml  (bundled)
      │        4. None → _DARK_FALLBACK
      │
      ├─ TOML inheritance: [meta] inherits = "<parent>"
      │        cycle guard via _seen frozenset; child [tokens] override parent
      │
      ├─ _apply_palette(app, tokens)   ← 10 tokens → QPalette roles
      │        Disabled group: text + ButtonText → text_dim
      │
      ├─ app.setStyleSheet(Template(_QSS_TMPL).substitute(tokens))
      │
      └─ bus.publish(ThemeChanged(name=name, tokens=tokens))
```

Bundled themes: `dark`, `light`, `catppuccin-mocha`.
User themes: drop `<name>.toml` into `~/.config/biome-fm/themes/`.
`_TOKENS` and `_QSS` are backward-compat aliases in `theme.py`.

### Overlay / Detachable Panel System (v0.8.0)

Preview and AI panels open in the pane *opposite* the active one.
`PanelManager` (pure Python, no Qt) owns the state and produces `Effect` objects.
`PanelCoordinator` (QObject) consumes Effects and drives Qt widgets.

```
User presses Space/F3 (preview) or Ctrl+I (AI)
      │
      ▼
PanelCoordinator.toggle(name, active_side)
      │
      ▼
PanelManager.toggle(name, active_side) → list[Effect]
      │
      ├─ Effect(show_overlay, target_side=opposite)
      │       hide pane widget on opposite side (_hidden_widget)
      │       show panel widget in its place
      │       save splitter sizes
      │
      ├─ Effect(set_opposite_visible, False)
      │       replaces right pane when active=left, left pane when active=right
      │
      └─ Effect(show_floating) — via View → Detach Preview / Detach AI
              panel detached into QDialog; pane widget restored
```

States: `HIDDEN → OVERLAY → FLOATING` (and back). Each named panel tracks its own state.
Session: `PanelSession(overlay_side)` saved to `session.json` so overlay side survives restart.

### Preview System (v0.7.0)

`Space` / `F3` → `PreviewPresenter.toggle_item()` → slide-in `PreviewPanel` (350px, 150ms OutCubic).
Cursor move → `update_if_visible()` (no-op if panel hidden).

```
FileItem
      │  Space / cursor-move
      ▼
PreviewPresenter
      ├─ cache hit (path, mtime) → PreviewPanel.show_result()        [sync]
      └─ cache miss:
             PreviewRegistry.find(path) → PreviewProvider
             ThreadPoolExecutor (max_workers=1)
                   │  [background thread]
                   ▼
             PreviewProvider.render(PreviewRequest) → PreviewResult
                   │  queue.SimpleQueue.put(result)
             QTimer.drain() — main thread
                   ▼
             PreviewPanel.show_result(result)
                   match ContentKind:
                     IMAGE    → QLabel.setPixmap (KeepAspectRatio)
                     HTML     → QTextBrowser.setHtml
                     TEXT     → QTextBrowser.setPlainText
                     MARKDOWN → QTextBrowser.setMarkdown
                     ERROR    → QTextBrowser.setPlainText "Error: ..."
```

Provider priority (ascending = higher wins; first `can_handle` match used):

| Provider | Priority | Extensions | Limit |
|---|---|---|---|
| ImagePreviewProvider | 0 | jpg/png/gif/webp/svg/bmp/tiff/ico | 50 MB |
| MarkdownPreviewProvider | 5 | .md/.markdown/.mdx/.mdown | 200 KB |
| TextPreviewProvider | 10 | .py/.js/.ts/.toml/.json + 20 more | 256 KB |
| FallbackProvider | 999 | * (always) | — |

Cache: 64 entries, key `(path, mtime)`. FIFO eviction (oldest dropped when full).
`ThemeChanged` event → `PreviewPresenter.set_dark()` so next render picks correct palette.
`models/markdown_renderer.render(md, dark)` is a Pygments-enhanced HTML path separate
from `MarkdownPreviewProvider` (which returns raw Markdown for `QTextBrowser.setMarkdown`).

### Plugin System Enhancements (v0.7.0)

8 hook specs; plugins implement any subset:

| Hook | Mode | Purpose |
|------|------|---------|
| `register_commands` | historic | Add CommandEntry to CommandRegistry at startup |
| `on_navigate` | broadcast | Pane navigated to path |
| `on_file_operation` | broadcast | Post-op notification (copy/move/delete/mkdir) |
| `provide_theme` | firstresult | Supply ThemeTokens for named theme |
| `before_file_operation` | firstresult | Veto op by returning False |
| `context_menu_actions` | broadcast | Inject ActionSpec items into context menu |
| `extra_columns` | broadcast | Inject ColumnDef into file listing |
| `extra_archive_extensions` | broadcast | Register extra archive extensions |

Loading order in `create_app()`:
1. `load_entry_points()` — installed packages (`biome_fm.plugins` entry_points group)
2. `load_local_plugins()` — `.py` files / dirs with `__init__.py` in `~/.config/biome-fm/plugins/`
3. Builtin plugins — `BuiltinDarkTheme` registered last

API versioning: `BIOME_FM_API_VERSION = (1, 0)` on plugin class.
Major mismatch → `warnings.warn` + skip. Minor is backward-compatible.
Local plugin contract: must expose top-level `Plugin` class; loaded as `biome_fm_local_<stem>`.

`ThemeRegistry(pm).resolve(name)` = thin helper that calls `provide_theme` firstresult
hook then merges over `_DARK_FALLBACK`; used in `theme.py`'s `load_theme()`.

### Async File Operations with Progress + Cancel (v0.9.0)

`ManagerPresenter.drop_files()` dispatches through an async path via `OpQueue`:

```
drop_files(paths, target_pane_id, move, target_folder)
      │
      ├─ resolve dest_dir (target_folder or pane's cwd)
      ├─ cancel = threading.Event()
      ├─ task_id = queue.next_task_id()
      ├─ cmd = ProgressCopyCmd / ProgressMoveCmd
      │         (sources, dest_dir, vfs, cancel, _noop_report)
      ├─ queue.submit(cmd, cancel=cancel, task_id=task_id)
      │         ThreadPoolExecutor._run():
      │           cmd.execute() → 256KB chunks → cancel.is_set() → raise Cancelled
      │           Cancelled → put(OpCancelled)
      │           done      → put(OpDone)
      └─ publish(AsyncOpSubmitted(task_id, desc, cancel))
               ▼
         app.py._on_async_op()
               ▼
         ProgressDialog(task_id, desc, parent=window)
               │  Cancel button → cancel.set()
               │  OpProgress events → update bars
               └─ OpDone / OpCancelled → dialog.close()
```

`ProgressCopyCmd.execute()` copies source-by-source; `_copy_file()` reads in 256KB
chunks, checks `cancel.is_set()` each chunk (partial file deleted on cancel).
`ProgressMoveCmd` calls `shutil.move` per file (atomic on same FS, copy+delete otherwise).
Both support undo: `CommandHistory.push(cmd)` records the already-executed command
after successful completion so Ctrl+Z can reverse it.

### Settings Window (v0.9.0)

`SettingsPresenter` is Qt-free; `SettingsViewProtocol` is a structural Protocol with
`set_*/get_*` methods for each config field. `SettingsDialog` (4-tab QDialog) implements
the protocol. `app.py` wires `Ctrl+,` → `_open_settings()` which creates a
`SettingsDialog`, a `SettingsPresenter(cfg, dialog, bus, plugin_manager)`, calls
`presenter.load()`, shows the dialog, and on `Accepted` calls `presenter.save()`.
`save()` persists to TOML and publishes events (`ShowHiddenToggled`, `ThemeChanged`)
as needed so the live UI reflects changes immediately.

### Toggle Hidden Files (v0.9.0)

`Ctrl+H` → `ManagerPresenter.toggle_hidden()` → flips `Config.show_hidden` →
publishes `ShowHiddenToggled(enabled)`. `app.py` subscribes: `_on_show_hidden(ev)`
calls `proxy.set_show_hidden(ev.enabled)` on every `DirSortFilterProxy` (both panes,
all tabs). `DirSortFilterProxy.filterAcceptsRow()` rejects dotfile names when
`_show_hidden=False`. Setting persisted to config on next `save_config()` call.

### Breadcrumb Path Bar (v0.11.0)

`BreadcrumbBar` replaces the old `_PathComboBox` in `PaneView._path_bar`. It owns a
`QStackedWidget` with two children: `_CrumbRow` (breadcrumb mode) and `_PathComboBox`
(edit mode). Clicking any segment navigates there; clicking the edit zone or pressing
a nav shortcut switches to edit mode.

```
PanePresenter.set_path(path)
      │
      ▼
PaneView.set_path(path) → BreadcrumbBar.set_path(path)
      │
      ├─ path_segments(path) → [(label, full_path), ...]   [pure, no Qt]
      │
      └─ _CrumbRow._rebuild() → clears old buttons, creates one _SegmentButton per segment
               │  click segment
               ▼
         BreadcrumbBar.path_entered.emit(str(full_path))
               ▼
         PaneView._on_path_entered_text(text) → path_change_requested.emit(Path(text))
```

Horizontal wheel/swipe on `_CrumbRow`: `wheelEvent` accumulates `angleDelta().x()`;
when abs(delta) >= 120 and cooldown (300ms) elapsed → emits `back_requested` (delta < 0)
or `forward_requested` (delta > 0). Tracks macOS trackpad momentum without spurious
repeat triggers.

RMB context menu on any segment button: Copy Path / Copy Name / Show in Finder /
Open Terminal Here (calls `platform.open_terminal(segment_path)`).

`path_segments(path)` is a pure function in `breadcrumb_bar.py` — no Qt, fully unit-tested.

### CLI AI Providers (v0.11.0)

`ai/cli/` wraps external CLI tools as `AIProviderProtocol` implementations without
requiring any Python SDK. Three builtins: `CLAUDE_CODE` (`claude`), `CODEX` (`codex`),
`OPENCODE` (`opencode`).

```
make_cli_providers()
      │
      ├─ for each BackendDef in [CLAUDE_CODE, CODEX, OPENCODE]:
      │       BackendDef.resolve_binary() → which(cmd) → Path | None
      │       found → CliProvider(backend) added to result dict
      │
      └─ result merged into make_providers(cfg) output
```

`CliProvider.chat_stream(messages, system)`:
1. `_build_prompt(messages, system)` → plain-text prompt string
2. `_backend.build_argv(prompt, model)` → argv list
3. `subprocess.Popen(argv, stdout=PIPE, text=True)` → line iterator
4. Each line → `stream_parse.parse_*_line(line)` → str token | None
5. Yields non-None tokens; `generator.close()` → `finally: proc.terminate()`

`stream_parse.py` handles per-backend quirks: claude-code emits JSON SSE lines that
are filtered; codex emits plain text; opencode uses a different JSON schema.

### MCP Server (v0.11.0)

`mcp/` exposes the file manager's VFS as a Model Context Protocol server. The server
runs over stdio transport (MCP standard) and is registered in AI tool client configs
via `biome-fm configure`.

```
biome-fm configure          # dispatched in __main__.py before Qt import
      │
      └─ mcp/cli.py::_configure(argv)
               │
               ├─ clients.detect_installed() → list of found client config files
               ├─ resolver.build_server_entry() → {"command": ..., "args": [...]}
               │       find_server_command():
               │           1. uvx run biome-fm-mcp   (preferred — isolated env)
               │           2. .venv/bin/biome-fm-mcp  (project venv)
               │           3. python -m biome_fm.mcp._entry  (fallback)
               └─ merger.merge_mcp_config(info, entry)
                       JSON clients: atomic write via tmp file + os.replace
                       TOML clients: tomlkit-based section merge

biome-fm-mcp                # separate entry point, no Qt
      │
      └─ mcp/_entry.py::main()
               └─ server.create_server(allowed_roots).run()   [stdio transport]
```

`create_server(allowed_roots)` builds a `FastMCP` instance. All tool functions call
`_validate_path(path_str, allowed_roots)` which resolves the path and checks
`is_relative_to()` against each allowed root — raises `ValueError` on traversal attempt.

Read tools (4): `list_directory`, `stat_item`, `read_file` (64 KB cap, binary detection),
`search_files` (glob, recursive flag).

Write tools (6): `copy_files`, `move_files`, `delete_files`, `make_directory`,
`rename_file`, `undo_last` — all executed via Command pattern + `CommandHistory`,
so undo is available within a session.
