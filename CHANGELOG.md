# Changelog

All notable changes to Biome FM are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.1.0] — 2025-07-11

### Added
- **PanePresenter** — Qt-free core navigation logic (navigate, go_up, go_home, go_root, go_back, go_forward, refresh, on_item_activated). History stack with back/forward. Dirs-first sorting, case-insensitive.
- **PaneViewProtocol** — Protocol contract (set_items, set_path, set_status, show_error) that keeps Presenter decoupled from Qt.
- **DirectoryModel** — QAbstractTableModel wrapping list[FileItem]. 4 columns: Name / Size / Modified / Ext. UserRole returns FileItem for proxy access.
- **DirSortFilterProxy** — QSortFilterProxyModel: ".." always first, dirs before files, substring filter.
- **PaneView** — Passive QWidget (QLineEdit path bar + QTableView). Emits item_activated and path_change_requested; implements PaneViewProtocol.
- Dual-pane DI wiring in app.py — two independent PanePresenter + PaneView pairs sharing one LocalVFS.
- MainWindow updated to accept left/right PaneView widgets via constructor injection.
- 55 tests total: 22 unit (no Qt), 11 + 8 integration (offscreen Qt), 7 + 7 existing.

### Fixed
- `FileItem.size_str` dead code in first loop of `_format_size`.
