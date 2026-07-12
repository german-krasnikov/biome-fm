# Biome FM Architecture

## Overview

```
src/biome_fm/
├── __main__.py         # CLI entry point: QApplication bootstrap, apply_theme, create_app()
├── app.py              # create_app() factory — full DI wiring (VFSRouter, Config,
│                       #   Session, Plugins, AI, CommandPalette, PaneSideViews);
│                       #   nav/DnD/context-menu signal wiring; focus tracking → active pane bus;
│                       #   toolbar signals (refresh/new_tab); _copy_path/_quick_look/_reveal_in_finder
│                       #   closures; Ctrl+Z/Ctrl+Shift+Z/F3/Ctrl+Shift+C/Ctrl+Shift+L shortcuts;
│                       #   _wire_pane() / _wire_ctx() / _new_tab() helpers
├── qt.py               # Centralised PySide6 imports (Anki pattern); includes QMimeData, QDrag
├── config.py           # @dataclass Config + TOML loader (save_config / load_config)
├── session.py          # SessionState / PaneSideState / TabState → JSON persistence
├── event_bus.py        # Decoupled pub/sub (EventBus singleton);
│                       #   events: FilesChanged, ActivePaneChanged, OperationStarted,
│                       #   OperationFinished, PaneNavigated, SyncBrowsingToggled,
│                       #   BookmarkChanged, ThemeChanged(name, tokens)
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
│   │                       #   set_filter(text) for Quick Filter
│   ├── bookmark_store.py   # TOML-backed list[Path]; add/remove/all/__contains__;
│   │                       #   reads/writes [bookmarks] paths = [...] via tomllib
│   ├── icon_provider.py    # icon_for_extension(ext) — @lru_cache(256), QFileIconProvider;
│   │                       #   icon_for_dir() — SP_DirIcon; fallback to SP_FileIcon
│   └── markdown_renderer.py # render(md, dark) → HTML for QTextBrowser.setHtml();
│                            #   QTextDocument.setMarkdown(GFM|NoHTML) → toHtml();
│                            #   Pygments replaces <pre> blocks (monokai dark / default light);
│                            #   @lru_cache(maxsize=2) on HtmlFormatter; 100KB truncation limit
│
├── presenters/
│   ├── pane_presenter.py     # Drives one pane (cd, select, sort, current_item);
│   │                         #   PaneViewProtocol: set_items/set_path/show_error/set_status/
│   │                         #   set_marked/current_cursor_item/advance_cursor/retreat_cursor/
│   │                         #   set_filter_visible;
│   │                         #   back/forward stacks; archive in-pane via _is_archive();
│   │                         #   _update_status: marks + free-space (cached disk_usage); _fmt_size;
│   │                         #   selection ops: toggle_mark/toggle_mark_up/select_all/
│   │                         #   deselect_all/invert_selection/select_by_pattern/deselect_by_pattern
│   ├── tabs_presenter.py     # Owns N PanePresenters per side; duck-types as PanePresenter
│   │                         #   for ManagerPresenter; TabsViewProtocol requires set_tab_tooltip;
│   │                         #   tabs display abbreviated path (~/... or …/name if >30 chars);
│   │                         #   tooltip = full str(path); opener param passed to each PanePresenter
│   ├── manager_presenter.py  # Inter-pane ops (copy, move, delete, mkdir, rename);
│   │                         #   drop_files(paths, target_pane_id, move) — DnD with path validation;
│   │                         #   toggle_mirror() / navigate_active() for Sync Browsing;
│   │                         #   undo/redo via CommandHistory → refresh_both()
│   ├── ai_presenter.py       # AI chat bridge (AIProvider ↔ AIChatViewProtocol)
│   ├── compare_presenter.py  # Directory diff (left vs right pane)
│   ├── rename_presenter.py   # Multi-rename (pattern, counter, ext substitution)
│   └── search_presenter.py   # File search (name glob + content grep)
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
│   │                     #   key routing: Space/F3=PreviewPanel toggle, Shift+Down=mark, Shift+Up=mark_up,
│   │                     #   /=FilterBar, printable→JumpBar; context menu: Copy/Move/Delete/
│   │                     #   Rename/Copy Path/Preview/Open in Finder (platform label);
│   │                     #   setUniformRowHeights() compat stub; table: no grid,
│   │                     #   alternatingRowColors, 22px rows, vertical header hidden;
│   │                     #   Name=Stretch, Size/Modified/Ext=Interactive;
│   │                     #   retreat_cursor() for Shift+Up mark; advance_cursor() for mark;
│   │                     #   10 signals: item_activated, path_change_requested,
│   │                     #   mark_toggle_requested, mark_toggle_up_requested, view_requested,
│   │                     #   back/forward/up/home_requested, files_dropped, context_action_requested
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
│   └── theme.py          # TOML-based theme system; load_theme(name) resolves plugin hook
│                          #   → TOML inheritance (meta.inherits) → _DARK_FALLBACK;
│                          #   _find_theme(): user AppConfig/biome-fm/themes/ first, then
│                          #   importlib.resources; _apply_palette() maps 10 tokens to QPalette;
│                          #   apply_theme(app, name, plugin_manager) publishes ThemeChanged;
│                          #   _TOKENS alias kept for backward compat; Template(_QSS_TMPL) fills QSS
│
├── commands/
│   ├── base.py           # Command ABC (execute/undo/undoable) + CommandHistory (50 levels)
│   ├── registry.py       # CommandRegistry + CommandEntry (id, name, shortcut, fn)
│   ├── copy_cmd.py       # CopyCmd (shutil.copy2)
│   ├── move_cmd.py       # MoveCmd
│   ├── delete_cmd.py     # DeleteCmd (send2trash)
│   ├── rename_cmd.py     # RenameCmd
│   ├── mkdir_cmd.py      # MkdirCmd
│   └── multi_rename_cmd.py # MultiRenameCmd (batch with pattern/counter)
│
├── operations/
│   ├── queue.py          # OpQueue: asyncio + ThreadPoolExecutor
│   └── task.py           # OpTask: priority, cancel, progress callback
│
├── preview/
│   ├── provider.py       # PreviewProvider Protocol (priority, can_handle, render);
│   │                     #   ContentKind enum (IMAGE/TEXT/HTML/MARKDOWN/ERROR);
│   │                     #   PreviewRequest(path, dark); PreviewResult(kind, data, title)
│   ├── registry.py       # PreviewRegistry: sorted list[PreviewProvider] by priority;
│   │                     #   find(path) → first match or FallbackProvider()
│   ├── presenter.py      # PreviewPresenter (Qt-free): ThreadPoolExecutor(max_workers=1);
│   │                     #   64-item LRU cache keyed (path, mtime); queue.SimpleQueue for
│   │                     #   thread→main delivery; drain() polled by QTimer;
│   │                     #   toggle_item(), update_if_visible(), set_dark(), shutdown()
│   └── providers/
│       ├── image.py      # ImagePreviewProvider (priority=0); jpg/png/gif/webp/svg etc; 50MB limit
│       ├── markdown.py   # MarkdownPreviewProvider (priority=5); .md/.markdown/.mdx; 200KB limit;
│       │                 #   returns ContentKind.MARKDOWN — panel calls QTextBrowser.setMarkdown
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
│   ├── provider.py       # AIProvider Protocol + NoOpProvider + make_provider factory
│   └── claude_provider.py # ClaudeProvider (anthropic SDK, streaming)
│
└── utils/
    ├── platform.py       # IS_MAC / IS_WIN / IS_LINUX; quick_look(path), quick_look_item(item),
    │                     #   reveal_in_finder(path), get_modifier_name() — cross-platform
    │                     #   (macOS: qlmanage -p / open -R; Windows: explorer /select; Linux: xdg-open)
    └── opener.py         # open_file(path) — default app opener (macOS: open, Win: os.startfile,
                          #   Linux: xdg-open); passed to TabsPresenter as opener=
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
VFSRouter walks path ancestry to detect archive roots (`.zip`, `.tar`, `.tar.gz`).
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

### AI Integration
AIProvider Protocol with NoOpProvider (default) and ClaudeProvider (optional).
Every feature works without AI. AIChatPanel is passive — emits message_submitted,
AIChatViewProtocol pushes responses in. AIPresenter bridges the two.
A 100ms QTimer drains the AI stream in `app.py`.

### Drag and Drop
`_PaneTableView` (inner class in pane_view.py) subclasses QTableView to override
`mimeData`/`startDrag`/`dragEnterEvent`/`dragMoveEvent`/`dropEvent`.
MIME type: `application/x-biome-fm-paths` (newline-joined absolute paths).
Drops emit `files_dropped(paths: list[Path], move: bool)` on `PaneView`
(move=True when Shift held during drop).
`app.py` wires this to `ManagerPresenter.drop_files(paths, target_pane_id, move)`,
which resolves paths, filters same-dir no-ops, then dispatches CopyCmd or MoveCmd.
`DirectoryModel.flags()` adds `ItemIsDragEnabled` — the root-cause fix that made DnD work.

### Active Pane Tracking
`app.py` tracks focus via `focusChanged` (QApplication signal).
The active `PaneSideView` receives `set_active(True)`, the inactive one `False`.
`set_active()` toggles QSS dynamic property `active`; `theme.py` applies a blue border.
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
