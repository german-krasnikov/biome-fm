# Changelog

All notable changes to Biome FM are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.17.2] — 2026-07-15

### Fixed
- **Breadcrumb swipe → scroll** — horizontal swipe on breadcrumb bar scrolls the path instead of
  triggering back/forward navigation; `back_requested`/`forward_requested` signals removed from
  `BreadcrumbBar`
- **Unified selection** — removed cell-level focus rectangle, `Cmd+Click` toggles mark without
  advancing cursor (`toggle_mark_at`), full-row selection only; QSS `outline: 0` on QTableView
- **TC-style cursor vs marks** — marked items show background color, cursor shows accent border
  around entire row (no fill); Qt selection state suppressed via delegate `initStyleOption`
- **Refresh preserves state** — 5-second auto-refresh and manual F5 preserve scroll position and
  marks in both panes (DRY via `preserve_scroll` kwarg on `set_items()`)
- **DnD multi-file with marks** — drag-and-drop uses app marks (like F5) instead of Qt
  `selectedIndexes`; `DirectoryModel.marks` property; `make_path_mime()` DRY helper
- **".." pinned first** — `DirSortFilterProxy.lessThan` checks `sortOrder()` so ".." stays at top
  regardless of ascending/descending sort; dirs-before-files also respects sort order

### Added
- **Breadcrumb drag** — dragging a breadcrumb segment creates `QDrag` via `make_path_mime()`;
  Finder receives folder URL, text editors receive path string
- `tests/unit/test_pane_mark_at.py` — 4 tests (toggle_mark_at)
- `tests/integration/test_focus_delegate.py` — 1 test (focus+selection stripping)
- `tests/unit/test_pane_refresh_cursor.py` — +1 test (refresh preserves marks)
- `tests/integration/test_breadcrumb_bar.py` — +2 tests (drag mime, drag_start init)
- `tests/integration/test_external_dnd.py` — +4 tests (marks-aware DnD)

## [v0.17.1] — 2026-07-15

### Added
- **Toolbar removed** — `QToolBar` (Refresh/+Tab/Preview/AI buttons) deleted; actions moved to
  menubar (File, View); macOS-only zero-height drag toolbar kept via `setUnifiedTitleAndToolBarOnMac`
- **"+" tab button in nav bar** — `_btn_new_tab` QPushButton at right of each pane's nav bar;
  `new_tab_requested` signal on `PaneView`; wired per-pane so each side creates tabs independently
- **Nav bar layout** — `[◄] [►] [▲] [★] | BreadcrumbBar(stretch) | [+]`; Home button removed
- **PaneSideView tab bar** — `_sync_tab_bar()`: hidden on single tab, shown with close buttons on 2+
- **Refresh cursor preservation** — `PanePresenter.refresh()` captures cursor before reload and
  restores it via `_navigate_no_history(path, initial_cursor=name)`; cursor stays after F5 or auto-refresh
- **`_op_items()` helper** — marked items → cursor fallback (TC behavior); used by F5/F6/F8 and action bar
- **New shortcuts** — `Ctrl+R` (refresh), `Ctrl+W` (close tab, File → Close Tab)
- **`close_tab_requested`** signal on `MainWindow` wired to File → Close Tab (`Ctrl+W`)
- **`refresh_timer`** — 5-second `QTimer` in `app.py` calls `manager._refresh_both()`, skipped
  while `_progress_dialogs` active
- **QSS cleanup** — ~23 lines of dead `QToolBar` CSS removed from `_base.qss.tmpl`

### Tests
- `tests/integration/test_plus_tab_button.py` — 4 tests (`_btn_new_tab` exists, emits signal,
  visible on single tab, `MainWindow` has no `QToolBar`)
- `tests/unit/test_op_items_fallback.py` — 4 tests (`_op_items` marked priority, cursor fallback,
  `..` excluded, None cursor)
- `tests/unit/test_pane_refresh_cursor.py` — 1 test (refresh preserves cursor via `initial_cursor`)
- `tests/integration/test_nav_icons.py` — removed `test_nav_home_signal` (Home button gone from nav bar)

## [v0.17.0] — 2026-07-14

### Added
- **TC-style bookmark tree** — `BookmarkNode` dataclass (`kind: Literal["dir","submenu","separator"]`,
  `path`, `name`, `children`); `BookmarkStore` redesigned from flat list to recursive tree
  (`_nodes: list[BookmarkNode]`); primary API: `tree()` / `set_tree(nodes)`; compat API unchanged
  (`add`, `remove`, `__contains__`, `all`, `get_name`, `set_name`, `display_label`); TOML format:
  `[[bookmarks.items]]` with `kind/path/name/depth` (flat+depth encodes nesting); migration from old
  flat `paths`/`names` arrays on first load; `BookmarkDialog` rebuilt as `_BookmarkTree(QTreeWidget)`
  with InternalMove DnD, Add Dir / Add Submenu / Add Separator / Delete / Rename / Up / Down buttons,
  `_sync_tree()` reads widget back to `BookmarkNode` list; `bookmark_menu.py` builds cascading
  `QMenu` recursively via `_build_menu(menu, nodes, signal)`; new tests:
  `test_bookmark_node.py` (9), `test_bookmark_store_tree.py` (20), `test_bookmark_dialog_tree.py` (10),
  `test_bookmark_menu_tree.py` (8)
- **Confirmation dialogs** — `ConfirmSpec` dataclass + injectable `confirm` callable in
  `ManagerPresenter`; guards on copy/move/drop and delete (red #danger button + "cannot be undone"
  warning); `ConfirmDialog` modal QDialog with path list (truncated at 5 items) and destination
  display; undo/redo bypass guard; 23 new tests (17 unit + 6 integration)
- Navigate to any folder always selects first item (`PanePresenter`)

### Fixed
- `ConfirmDialog` labels use `Qt.TextFormat.PlainText` to prevent HTML injection in paths

## [v0.16.1] — 2026-07-13

### Added
- **Glass opacity slider** — `cfg.glass_opacity` (int, default 47) persisted to TOML; Settings →
  Appearance → Opacity QSlider (range 10-90, step 5) drives `_apply_glass_alpha(tokens, opacity_pct)`
  and `_apply_palette()` as a single multiplier for all translucent elements

### Fixed
- Markdown code blocks semi-transparent in glass mode
- MD preview transparent body + opaque QMenu in glass mode
- Splitter context menu (RMB) + wider handle with hover accent
- Larger action bar buttons, zero gap to command line

## [v0.16.0] — 2026-07-13

### Added
- **Glass / frosted-glass mode** — native macOS blur via pyqt-liquidglass, `_GlassClearFilter` on
  all translucent widgets, `GlassStyle(QProxyStyle)`, semi-transparent surface tokens, Settings toggle
- **Global search** — `SearchDialog` + `SearchResultsPanel` + `SearchPresenter` with streaming results
- **DnD improvements** — self-copy guard via `Path.is_relative_to()`, Alt=Move modifier,
  outbound drag to external apps (uri-list + text/plain)
- **Bookmark dialog** — DnD support, Add/Rename/Remove, display names, file bookmark navigation
- **AI chat** — markdown rendering, biome: path hyperlinks, CLI providers, streaming, cancel
- **BreadcrumbBar** — scroll + arrows, RMB context menu, swipe navigation
- 946 tests, 0 failures

## [v0.15.0] — 2026-07-13

### Added
- **Glass / frosted-glass mode** — macOS NSVisualEffectView blur via `pyqt-liquidglass` ([glass]
  optional extra); `views/glass.py` thin wrapper (`prepare_glass`/`enable_glass`/`disable_glass`);
  `views/glass_style.py` provides `GlassStyle(QProxyStyle)` (wraps Fusion, skips opaque fills for
  glass-tagged widgets) + `mark_glass`/`unmark_glass` + `_GlassClearFilter(QObject)` event filter
  (CompositionMode_Clear before paint, installed on viewport for `QAbstractScrollArea`, on widget
  itself for everything else); `views/theme.py` `_apply_glass_alpha()` makes surface tokens
  semi-transparent (`_GLASS_ALPHA=120`, `_GLASS_SELECTION_ALPHA=140`), `base_bg=transparent`,
  `selection_bg` recolored; QPalette `Base`/`AlternateBase`/`Button`/`Highlight` get alpha;
  `PaneView.scrollContentsBy` calls `viewport().update()` to avoid ghost pixels in glass mode;
  toggled via Settings → Appearance → Glass checkbox (`cfg.glass`)
- **DnD self-copy guard** — `ManagerPresenter` blocks dropping a folder into itself or any of its
  subdirectories via `Path.is_relative_to()`; 3 new unit tests in `test_dnd_folder.py`
- **Alt=Move modifier** — `_MOVE_MODS = Qt.ShiftModifier | Qt.AltModifier` in `pane_view.py`;
  Alt held during drop or Alt-drag to text editors send text-only MIME (no URLs, macOS constraint);
  1 new integration test (`test_alt_drag_no_urls`)
- 28 new tests (7 `test_glass_theme.py` + 4 `test_glass_platform.py` + 9 `test_glass_style.py` +
  4 `test_settings_glass.py` + 3 `test_dnd_folder.py` + 1 `test_external_dnd.py`); 946 tests total

## [v0.14.3] — 2026-07-13

### Added
- **Outbound drag-and-drop to external apps** — `PaneView.mimeData()` sets all three MIME types
  simultaneously: internal `application/x-biome-fm-paths`, `text/uri-list` (Finder/Explorer/desktop),
  and `text/plain` (text editors and terminals); `..` entries excluded from URL list
- 5 tests (`test_external_dnd.py`); 918 tests total

## [v0.14.2] — 2026-07-13

### Added
- **Bookmark default names** — `display_label()` now returns `path.name` as fallback (computed,
  not stored in TOML); all bookmark items display "Name — /path" without requiring an explicit rename
- **File bookmark navigation** — clicking a file bookmark navigates the active pane to the parent
  directory and selects the file (`select_item(filename)`) instead of navigating into the file
- 9 new tests (3 `test_bookmark_store.py` + 4 `test_bookmark_navigation.py` + 2 `test_bookmark_dialog.py`);
  913 tests total

## [v0.14.1] — 2026-07-13

### Added
- **Bookmark names** — `BookmarkStore` gains `_names: dict[str, str]`, `get_name()`, `set_name()`,
  `display_label()`; TOML persists a parallel `names = [...]` array; corrupt TOML silently resets names
  without crashing; `BookmarkDialog` "Rename" button calls `set_name()` and refreshes list items as
  "Name — /path"; `bookmark_menu.py` uses `display_label()` so named bookmarks show their label
- **AI model persistence for all providers** — `_model_fields` in `app.py` now covers all 6 providers
  (`claude`, `openai`, `ollama` + 3 CLI); `_on_provider_changed` saves `ai_default_provider` to
  `config.toml` immediately on every provider switch (not just at app close)
- 3 new tests (`test_bookmark_store.py`: `replace_carries_name`, `name_with_quotes_roundtrip`,
  `corrupt_toml_does_not_crash`); 904 tests total

## [v0.14.0] — 2026-07-13

### Added
- **Bookmark dialog enhancements** — `BookmarkDialog` is now a non-modal `Qt.WindowType.Tool`
  singleton (singleton ref in `app.py._bm_dialog`; toggle show/raise instead of `.exec()`);
  "Add" button opens `QInputDialog.getText` → `Path(text).expanduser()` → `store.add()`; accepts
  DnD of `application/x-biome-fm-paths` and `text/uri-list`, guarding against empty and duplicate paths
- **"Add to Bookmarks" context menu** — `PaneView` context menu exposes "Add to Bookmarks" for
  files and folders; dispatched through `app.py:_on_add_bookmark()`
- 17 tests (13 `test_bookmark_dialog.py` + 4 `test_bookmark_menu.py`)

## [v0.13.1] — 2026-07-13

### Fixed
- **Breadcrumb disappears after repeated navigation** — `_SegmentButton` click handler changed
  from lambda closure to `_emit_navigated()` bound method (prevents stale captures); `_CrumbRow.set_path()`
  now passes `parent=self` to child widgets and defers `adjustSize()` via `QTimer.singleShot(0, ...)`
  so Qt can polish new buttons before sizing; `BreadcrumbBar.set_path()` chains a 10ms timer for
  `scroll_to_end` to run after the deferred resize
- **AI chat bubbles merging + typing indicator misaligned** — `_insert_clean_block()` static helper
  in `_chat_log.py` inserts a default `QTextBlockFormat` block before every `insertHtml()`, resetting
  alignment inherited from the previous bubble; all roles (`append_bubble`, `show_thinking`,
  `stream_start`) use this helper; `_tick_dots()` changed `<div>` → `<span>` inside existing block
- 881 tests (up from 877)

## [v0.11.0] — 2026-07-13

### Added
- **MCP Server** — `biome-fm-mcp` stdio entry point exposes 10 file-operation tools via
  FastMCP (`mcp/server.py`); path validation restricts tools to allowed roots; 4 read tools
  (`list_directory`, `stat_item`, `read_file`, `search_files`) + 6 write tools (`copy_files`,
  `move_files`, `delete_files`, `mkdir`, `rename_file`, `undo_last`)
- **AI CLI client registration** — `biome-fm configure/doctor/uninstall` CLI subcommands
  register/verify/remove the MCP server in 8 AI tool configs (claude-code, claude-desktop,
  cursor, windsurf, vscode, opencode, codex, kimi); `merger.py` writes JSON/TOML atomically;
  `resolver.py` finds server command via uvx → venv → `python -m`; dispatched from
  `__main__.py` before any Qt import so CLI works headlessly
- **CLI AI providers** (`ai/cli/`) — `CliProvider` wraps claude-code, codex, opencode via
  `subprocess.Popen`, implementing `AIProviderProtocol`; `stream_parse.py` normalises stdout
  per CLI; `make_cli_providers()` includes only backends whose executables are on PATH;
  `make_providers()` now discovers CLI providers alongside SDK providers
- **Breadcrumb Path Bar** — `BreadcrumbBar` (`views/breadcrumb_bar.py`) replaces the old
  `_PathComboBox` in `PaneView`; segments rendered as `_SegmentButton` (QToolButton) in
  `_CrumbRow`; click segment = navigate; RMB context menu: Copy Path / Copy Name /
  Show in Finder / Open Terminal Here (`utils/platform.py:open_terminal`); horizontal
  swipe/wheel on bar triggers back/forward (threshold 120, 300ms cooldown); `Alt+[` / `Alt+]`
  keyboard shortcuts for back/forward added in `app.py`; inline edit mode on double-click
- 792 tests (up from 694)

## [v0.10.0] — 2026-07-12

### Added
- **Syntax-highlighted code preview** — `CodePreviewProvider` (priority=8) uses Pygments to
  render 50+ languages as HTML; `monokai` theme in dark mode, `friendly` in light;
  `get_lexer_for_filename()` for language detection; files > 512 KB truncated; line count in title
- **Markdown renderer wired** — `MarkdownPreviewProvider` now calls `markdown_renderer.render()`
  instead of returning raw Markdown; dark/light-aware CSS injected for headings, code, tables,
  blockquotes; Pygments highlights fenced code blocks
- **PRE regex fix** — `PRE_GROUP_RE` in `markdown_renderer` no longer uses `+` grouping that
  caused missed replacements on consecutive pre blocks
- `pygments>=2.14` added to dependencies
- Preview cache key now includes `dark` flag — theme changes invalidate cached results
- Markdown rendering explicitly on Qt main thread (fixes potential QTextDocument crash in worker)
- 694 tests (up from 680)

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
