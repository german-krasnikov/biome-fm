# Changelog

All notable changes to Biome FM are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
