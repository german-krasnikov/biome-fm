# Changelog

All notable changes to Biome FM are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.5.0] — 2026-07-12

### Added

**11 Killer Features**
- Quick Filter (`/` key) — `FilterBar` inside `PaneView`; substring match via `DirSortFilterProxy`
- Copy Path (`Ctrl+Shift+C`) — copies absolute path to clipboard
- Undo/Redo UI (`Ctrl+Z` / `Ctrl+Shift+Z`) — wired to `ManagerPresenter.undo/redo`
- Sync Browsing (`Ctrl+Shift+L`) — mirrors navigation across panes; `SyncBrowsingToggled` event
- Quick Look (`Space` / `F3`) — OS-native preview (macOS / Windows / Linux)
- File Type Coloring — Okabe-Ito colorblind-safe palette by extension group
- Bookmarks (`Ctrl+D`) — `BookmarkStore` with TOML persistence
- Type-to-Nav — `JumpBar` scrolls to first matching name prefix on printable keys
- Archive In-Pane — `.tar`/`.zip` browsing without extraction via `VFSRouter`
- Opener Rules — per-extension launch rules from config; platform default fallback
- Nav Icons — Back/Forward/Up/Home use `QStyle.StandardPixmap`

**macOS UI Overhaul**
- System-color dark theme (NSColor tokens via QSS)
- Global toolbar (Refresh, +Tab, AI toggle)
- `_HistoryLineEdit` — 30-item dedup history with Up/Down + QCompleter (15 visible)
- `_PathTabBar` — abbreviated path display; Ctrl/middle-click copies full path
- `DirectoryModel.flags()` — `ItemIsDragEnabled` (DnD root-cause fix) + `ToolTipRole`
- DnD Shift-move: `dropEvent` reads modifiers instead of `proposedAction()`
- Context menu: Copy Path, Quick Look, Open in Finder/Explorer
- Nav/ActionBar tooltips on all buttons
- `platform.py` — `quick_look()`, `reveal_in_finder()` cross-platform

**UX Polish**
- Table layout: hidden vertical header, alternating rows, no grid, uniform 22px rows
- Column resize: Name=Stretch, Size/Modified/Ext=Interactive
- Dynamic tab close button (visible only when >1 tab)
- Key bindings: Space=preview, Shift+Down/Up=mark toggle with retreat cursor
- Command line: visible by default, dropdown history, executes shell commands
- AI button in toolbar (checkable QAction, Ctrl+I)

**New modules:** `filter_bar.py`, `jump_bar.py`, `bookmark_store.py`, `icon_provider.py`, `opener.py`, `platform.py`
**New EventBus events:** `PaneNavigated`, `SyncBrowsingToggled`, `BookmarkChanged`
**New config fields:** `sync_browsing`, `file_type_colors`, `show_hidden`, `bookmarks`, `openers`
**Tests:** 410 (up from 322)

### Fixed
- DnD drag never started — `flags()` missing `ItemIsDragEnabled`
- Tab titles showed raw `path.name`; now abbreviated `~/...`
- `_run_cmd` no longer swallows stdout to DEVNULL
- Initial tab formatted correctly via `add_tab("")` + `navigate_to`

## [v0.3.0] — 2026-07-11

### Added
- Navigation toolbar per pane — Back / Forward / Up / Home buttons with Alt+← / Alt+→ / Alt+↑ / Alt+Home shortcuts
- Drag & drop between panels — copy on drop (Ctrl held = move); path validation rejects invalid targets
- Right-click context menu — Copy / Move / Delete / Rename actions on selected items
- Active pane border highlight — focused pane gets a colored border for clear visual tracking
- MenuBar — File / Edit / Navigate / View menus wired to presenter actions and shortcuts
- Enhanced status bar — shows marked file count + total size of marks, plus free disk space for current path
- Column sorting — click any header (Name / Size / Modified / Ext) to sort; second click reverses order
- Command line hidden by default; toggled via View menu (Ctrl+G)
- 322 unit + integration tests (up from 300)

### Fixed
- Layout: panes now fill the full available window space instead of collapsing to minimum size

## [v0.2.0] — 2025-07-11

### Added

**Phase 8 — Full Integration**
- `PaneSideView` — QTabBar + QStackedWidget tabbed pane container (left / right side each gets one)
- `AIChatPanel` — passive AI chat widget; emits `message_submitted`, implements `AIChatViewProtocol`
- `MainWindow` updated with `closeEvent` (session save on quit), `toggle_ai_panel`, `splitter_sizes` persistence
- `app.py` full rewrite: DI wires VFSRouter, Config, Session, PluginManager, AIPresenter, CommandPalette, TabsPresenters, and both PaneSideViews in one place
- `PanePresenter.current_item()` public method; `TabsPresenter.current_item()` delegates to active tab
- Integration tests for PaneSideView, AIChatPanel, and MainWindow close path (300 tests total, 0 lint errors)

**Phase 7 — Config / Session Persistence + TabsPresenter**
- `config.py` / `session.py` — TOML config and JSON session (paths, geometry, open tabs) saved/restored across restarts
- `SessionState`, `PaneSideState`, `TabState` dataclasses
- `TabsPresenter` — manages N PanePresenters per side; open/close/switch tab

**Phase 6 — Plugin System + VFS Adapters**
- `plugins/hookspecs.py` / `plugins/manager.py` — pluggy hook system, entry_points discovery
- `models/vfs_router.py` — VFSRouter dispatches by URI scheme
- `models/archive_vfs.py` — ZIP and TAR.GZ browsing via fsspec

**Phase 5 — AI Provider Protocol + Claude Integration**
- `ai/provider.py` — AIProvider Protocol, NoOpProvider (default), `make_provider` factory
- `ai/claude_provider.py` — ClaudeProvider backed by anthropic SDK (streaming)
- `presenters/ai_presenter.py` — bridges AIProvider ↔ AIChatViewProtocol

**Phase 4 — Power Tools (Dir Compare, Multi-Rename, Search)**
- `presenters/compare_presenter.py` — directory diff (left vs right pane, symmetric diff)
- `presenters/rename_presenter.py` — multi-rename with pattern, counter, extension substitution
- `commands/multi_rename_cmd.py` — undoable batch rename
- `presenters/search_presenter.py` — file search (name glob + content grep)

**Phase 3 — Dark Theme, Command Palette, Command Registry**
- `views/theme.py` — dark/light palette + stylesheet switcher
- `views/command_palette.py` — fuzzy-search command launcher (Ctrl+Shift+P)
- `commands/registry.py` — CommandRegistry + CommandEntry (id, name, shortcut, callable)

**Phase 2 — TC-Style Marks, ActionBar, Keyboard Shortcuts**
- Total Commander–style file marking (Ins key, numpad *, numpad +/-)
- `views/action_bar.py` — F1-F10 function key bar
- Full keyboard shortcut wiring (F5 copy, F6 move, F8 delete, F7 mkdir, Tab switch pane)

**Phase 1 — Foundation (EventBus, Commands, Operations, ManagerPresenter)**
- `event_bus.py` — decoupled pub/sub EventBus
- `commands/base.py` — Command ABC + CommandHistory (50 levels)
- `commands/copy_cmd.py`, `move_cmd.py`, `delete_cmd.py`, `rename_cmd.py`, `mkdir_cmd.py`
- `operations/queue.py` / `operations/task.py` — OpQueue (asyncio + ThreadPoolExecutor) + OpTask
- `presenters/manager_presenter.py` — inter-pane ops, conflict resolution, progress delegation

**Phase 0 — Initial Scaffold (PanePresenter, Models, PaneView)**
- `PanePresenter` — Qt-free core navigation logic (navigate, go_up, go_home, go_root, go_back, go_forward, refresh, on_item_activated). History stack with back/forward. Dirs-first sorting, case-insensitive.
- `PaneViewProtocol` — Protocol contract (set_items, set_path, set_status, show_error) that keeps Presenter decoupled from Qt.
- `DirectoryModel` — QAbstractTableModel wrapping list[FileItem]. 4 columns: Name / Size / Modified / Ext. UserRole returns FileItem for proxy access.
- `DirSortFilterProxy` — QSortFilterProxyModel: ".." always first, dirs before files, substring filter.
- `PaneView` — Passive QWidget (QLineEdit path bar + QTableView). Emits item_activated and path_change_requested; implements PaneViewProtocol.
- Dual-pane DI wiring in `app.py` — two independent PanePresenter + PaneView pairs sharing one LocalVFS.
- MainWindow accepts left/right PaneView widgets via constructor injection.

### Fixed
- `FileItem.size_str` dead code in first loop of `_format_size`.
