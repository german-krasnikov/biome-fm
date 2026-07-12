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
│                       #   OperationFinished, PaneNavigated, SyncBrowsingToggled, BookmarkChanged
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
│   └── icon_provider.py    # icon_for_extension(ext) — @lru_cache(256), QFileIconProvider;
│                           #   icon_for_dir() — SP_DirIcon; fallback to SP_FileIcon
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
│   │                     #   key routing: Space=Quick Look, Shift+Down=mark, Shift+Up=mark_up,
│   │                     #   /=FilterBar, printable→JumpBar; context menu: Copy/Move/Delete/
│   │                     #   Rename/Copy Path/Quick Look/Open in Finder (platform label);
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
│   └── theme.py          # macOS system-color tokens (13 named values); dark QSS via Template;
│                          #   PaneSideView[active="true/false"] border; compact ActionBar buttons;
│                          #   toolbar QSS; apply_theme(QApplication) entry point
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
├── plugins/
│   ├── hookspecs.py      # pluggy @hookspec: fm_register_opener, fm_context_menu_items
│   └── manager.py        # PluginManager: entry_points discovery + registration
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
`fm_register_opener`, `fm_context_menu_items`.
Discovery via `importlib.metadata.entry_points(group="biome_fm.plugins")`.

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
