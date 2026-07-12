# Changelog

All notable changes to Biome FM are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.9.1] — 2026-07-12

### Added
- **Enter/Return key activation** — `Enter`/`Return` in `_PaneTableView` emits `item_activated`
  (same as double-click): file→open with system program, folder→enter, `..`→go up,
  archive→browse in-pane. Numpad Enter also works.
- **`go_up()` cursor placement** — after navigating up, cursor lands on the folder the user
  came from (classic FM UX); implemented via new `PaneView.select_item(name)` +
  `PaneViewProtocol.select_item`
- **Initial focus** — left pane table receives focus at startup
- 680 tests (up from 667)

### Fixed
- Removed `.7z` from `_ARCHIVE_SUFFIXES` — VFS doesn't support it, caused OSError on activation
- `opener.open_file()` now guards against virtual archive paths (calls `set_status`, not `show_error`)

## [v0.9.0] — 2026-07-12

### Added
- **Toggle Hidden Files (`Ctrl+H`)** — `DirSortFilterProxy.set_show_hidden(bool)` filters dotfiles;
  `ManagerPresenter.toggle_hidden()` flips `Config.show_hidden` and publishes `ShowHiddenToggled`;
  persisted to config; both panes/all tabs updated via `app.py` EventBus subscriber
- **Enhanced Active Pane Highlight** — 3px left accent border + 1px top accent border replaces
  the previous 1px all-sides border; inactive pane uses transparent borders of same width
  to prevent layout shift
- **DnD Folder Highlight + Drop-to-Folder** — `_DropHintDelegate` draws 2px highlight rect
  around folder under cursor during drag; `_drop_hint_row` tracks it; dropping on a folder
  drops into it (`target_folder` arg); `files_dropped` signal is now 3-arg
  `(list[Path], bool, Path | None)`
- **File Operation Progress + Cancel** — `ProgressCopyCmd` (256KB chunks) and `ProgressMoveCmd`
  with `cancel: threading.Event` and `report` callback; `Cancelled` exception; `OpCancelled`
  event; `CommandHistory.push()` records already-executed commands; `OpQueue.submit()` accepts
  external cancel + task_id; `ProgressDialog` (modeless) shows per-file + overall progress bars
  with Cancel button; `AsyncOpSubmitted` event wires presenter → dialog in `app.py`
- **Settings Window (`Ctrl+,`)** — `SettingsPresenter` (Qt-free) + `SettingsViewProtocol` +
  `SettingsDialog` (4 tabs: General / Appearance / AI / Plugins); saves to TOML and publishes
  live events on accept
- 667 tests (up from 628)

## [v0.8.0] — 2026-07-12

### Added
- **Multi-model AI chat** — `AIProviderProtocol` with `chat_stream()` for streaming; `ClaudeProvider`, `OpenAIProvider`, `OllamaProvider`; model selector dropdown in AI panel
- **AI chat panel redesign** — `ChatLog` (bubble-style HTML with token-by-token streaming), `ContextBar` (DnD file attachment chips), `ai/types.py` (`FileContent`, `ImageContent`)
- **Opposite-pane overlay** — Preview/AI panels now open in the pane opposite the active one (active left → overlay replaces right; active right → overlay replaces left)
- **PanelManager** (`panel_manager.py`) — pure-Python state machine; states HIDDEN/OVERLAY/FLOATING; produces `Effect` objects (no Qt dependency; fully unit-tested)
- **PanelCoordinator** (`views/panel_coordinator.py`) — QObject that dispatches Effects to Qt widgets; accepts `left_side` + `right_side`; `toggle(name, active_side)` drives overlay placement; `_saved_sizes` restores splitter on hide; `_hidden_widget` tracks displaced pane
- **Detachable panels** — Preview and AI panels can be torn off into floating `QDialog` windows via View → Detach Preview / Detach AI
- **Session persistence** — `PanelSession.overlay_side` field in `session.py` survives restarts
- **Splitter handle context menu** — right-click or middle-click on splitter handle for 25/75, 50/50, 75/25 pane ratios
- 628 tests (up from 531)
- `tests/unit/test_panel_manager.py`, `tests/unit/test_ai_providers.py`, `tests/unit/test_ai_types.py`
- `tests/integration/test_panel_coordinator.py`, `tests/integration/test_overlay_panels.py`

## [v0.7.0] — 2026-07-12

### Added
- **TOML-based theme system** — dark, light, catppuccin-mocha; `_base.qss.tmpl` template with token substitution
- **Theme inheritance** — `inherits` key in TOML cascades tokens from parent theme
- **User theme directory** — `~/.config/biome-fm/themes/` auto-loaded at startup
- **QPalette sync** — native dialogs inherit active theme colors via `QApplication.setPalette`
- **Inline preview panel** — Space/F3 now opens a slide-in panel instead of external Quick Look
- **Markdown preview** — native GFM rendering via `QTextBrowser.setMarkdown`; `MarkdownRenderer` model
- **Image preview** — JPG, PNG, GIF, WebP, SVG, BMP via `QPixmap`
- **Text preview** — first 256 KB shown; `TextPreviewProvider`
- **Metadata fallback preview** — for unsupported file types; `FallbackPreviewProvider`
- **Preview panel animation** — `QPropertyAnimation` slide-in/out on panel show/hide
- **6 new plugin hookspecs** — `provide_theme`, `before_file_operation`, `after_file_operation`, `context_menu_actions`, `extra_columns`, `extra_archive_extensions`
- **Historic hook support** — `register_commands` hookspec upgraded to `historic=True`
- **Plugin API versioning** — `PLUGIN_API_VERSION` constant; major-version gate rejects incompatible plugins
- **Drop-in local plugin loading** — `~/.config/biome-fm/plugins/` scanned at startup via `importlib`
- **BuiltinDarkTheme reference plugin** — `plugins/builtin/dark_theme.py`
- **ThemeRegistry** — singleton mapping plugin-provided theme names to TOML dicts; `plugins/theme_registry.py`
- `preview/` package — `PreviewProvider` protocol, `PreviewRegistry`, `PreviewPresenter`; providers for markdown, image, text, fallback
- `plugins/types.py` — shared plugin type definitions (`ThemeDict`, `ContextMenuAction`, etc.)

### Fixed
- macOS: QSS rules for `QPushButton` and `QComboBox` now apply correctly (`setStyle("Fusion")` in `app.py`)
- Archive detection regression for `.gz` files in `VFSRouter.is_archive`

### Changed
- Space/F3 opens inline `PreviewPanel` instead of calling `platform.quick_look()`
- Theme system refactored from hardcoded QSS strings in `theme.py` to TOML token files + `_base.qss.tmpl`

## [v0.6.0] — 2026-07-12

### Added
- **Path History Dropdown** — `_PathComboBox` replaces QLineEdit in PaneView nav bar; per-pane navigation history (60 stored, 30 visible); dedup move-to-front on revisit
- **Bookmarks Dropdown** — ★ QToolButton with InstantPopup QMenu in each pane's nav bar; click to navigate, menu rebuilds on `aboutToShow`
- **Bookmark Edit Dialog** — QDialog with QListWidget + Remove/Up/Down/Edit Path/Close buttons; live mutations persist immediately to TOML
- `BookmarkStore.move_up()`, `move_down()`, `replace()` methods
- `PanePresenter._nav_history` with `nav_history` property and `set_nav_history` protocol method
- `Ctrl+D` toggles bookmark for current path + publishes `BookmarkChanged`
- 431 tests (up from 410)

### Fixed
- `BookmarkDialog._refresh()` preserves selection row after mutations
- `move_up`/`move_down` guard against path not in store (no ValueError)

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
