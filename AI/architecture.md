# Biome FM Architecture

## Overview

```
src/biome_fm/
├── __main__.py         # CLI entry point: QApplication bootstrap, apply_theme, create_app()
├── app.py              # create_app() factory — full DI wiring (VFSRouter, Config,
│                       #   Session, Plugins, AI, CommandPalette, PaneSideViews);
│                       #   nav/DnD/context-menu signal wiring; focus tracking → active pane bus
├── qt.py               # Centralised PySide6 imports (Anki pattern); includes QMimeData, QDrag
├── config.py           # @dataclass Config + TOML loader (save_config / load_config)
├── session.py          # SessionState / PaneSideState / TabState → JSON persistence
├── event_bus.py        # Decoupled pub/sub (EventBus singleton)
│
├── models/
│   ├── file_item.py        # FileItem frozen dataclass
│   ├── vfs.py              # VFSProtocol + LocalVFS
│   ├── vfs_router.py       # VFSRouter: scheme → VFS dispatch (local/archive/…)
│   ├── archive_vfs.py      # ZIP/TAR.GZ VFS via fsspec
│   └── directory_model.py  # QAbstractTableModel + DirSortFilterProxy
│
├── presenters/
│   ├── pane_presenter.py     # Drives one pane (cd, select, sort, current_item);
│   │                         #   _update_status: marks + free-space (cached disk_usage); _fmt_size
│   ├── tabs_presenter.py     # Owns N PanePresenters per side; current_item delegation
│   ├── manager_presenter.py  # Inter-pane ops (copy, move, delete target selection);
│   │                         #   drop_files(paths, target_pane_id, move) — DnD handler with path validation
│   ├── ai_presenter.py       # AI chat bridge (AIProvider ↔ AIChatViewProtocol)
│   ├── compare_presenter.py  # Directory diff (left vs right pane)
│   ├── rename_presenter.py   # Multi-rename (pattern, counter, ext substitution)
│   └── search_presenter.py   # File search (name glob + content grep)
│
├── views/
│   ├── main_window.py    # QMainWindow: splitter, AI panel toggle, closeEvent,
│   │                     #   splitter_sizes persistence, _build_menubar, 4 nav signals
│   ├── pane_side_view.py # QTabBar + QStackedWidget — tabbed pane container;
│   │                     #   set_active(bool) for dynamic border highlight
│   ├── pane_view.py      # QWidget: path bar + nav buttons (←→↑⌂) + QTableView + filter;
│   │                     #   DnD via _FileTableView (mimeData/startDrag/dropEvent);
│   │                     #   context menu; 8 signals: item_activated, path_change_requested,
│   │                     #   mark_toggle_requested, back/forward/up/home_requested,
│   │                     #   files_dropped, context_action_requested
│   ├── ai_chat_panel.py  # Passive AI chat (message_submitted Signal)
│   ├── action_bar.py     # F1-F10 function key bar
│   ├── command_palette.py # Fuzzy-search command launcher
│   └── theme.py          # Dark/light palette + stylesheet; PaneSideView active/inactive border QSS
│
├── commands/
│   ├── base.py           # Command ABC + CommandHistory (50 levels)
│   ├── registry.py       # CommandRegistry + CommandEntry (id, name, shortcut, fn)
│   ├── copy_cmd.py       # CopyCommand (shutil.copy2)
│   ├── move_cmd.py       # MoveCommand
│   ├── delete_cmd.py     # DeleteCommand (send2trash)
│   ├── rename_cmd.py     # RenameCommand
│   ├── mkdir_cmd.py      # MkdirCommand
│   └── multi_rename_cmd.py # MultiRenameCommand (batch with pattern/counter)
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
    └── platform.py       # IS_MAC / IS_WIN / IS_LINUX, OS helpers
```

## Patterns

### Hybrid Supervising Controller (MVP variant)
Views emit signals → Presenters react → update Models → push state to Views.
Views NEVER import models. Presenters have ZERO Qt imports — testable with plain Python mocks.
Model is a thin data adapter (QAbstractTableModel wrapping list[FileItem]).

### Command + Undo
Every file mutation = Command(execute + undo). CommandHistory (50 levels).
CommandRegistry maps string ids to callables for CommandPalette dispatch.

### VFS Host Chaining
VFSRouter dispatches by URI scheme: `file://` → LocalVFS, `zip://` / `tar://` → ArchiveVFS.
Nested archives supported via chained VFS instances.

### Plugin Hooks (pluggy)
`fm_register_opener`, `fm_context_menu_items`.
Discovery via `importlib.metadata.entry_points(group="biome_fm.plugins")`.

### Multi-Tab Panes
Each side (left/right) has a PaneSideView (QTabBar + QStackedWidget) driven by a TabsPresenter owning N PanePresenters. Tabs are persisted to session.json via SessionState.

### AI Integration
AIProvider Protocol with NoOpProvider (default) and ClaudeProvider (optional).
Every feature works without AI. AIChatPanel is passive — emits message_submitted,
AIChatViewProtocol pushes responses in. AIPresenter bridges the two.

### Drag and Drop
`_FileTableView` (inner class in pane_view.py) subclasses QTableView to override
`mimeData`/`startDrag`/`dragEnterEvent`/`dragMoveEvent`/`dropEvent`.
Drops emit `files_dropped(paths: list[Path], move: bool)` on `PaneView`.
`app.py` wires this to `ManagerPresenter.drop_files(paths, target_pane_id, move)`,
which validates paths and dispatches CopyCommand or MoveCommand.

### Active Pane Tracking
`app.py` tracks focus via `focusChanged` (QApplication signal).
The active `PaneSideView` receives `set_active(True)`, the inactive one `False`.
`theme.py` applies a distinct border QSS so the user always sees which pane is active.
`ManagerPresenter.set_active_pane(pane_id)` keeps the presenter layer in sync for
operations that target the opposite pane.

### Nav Bar
`PaneView` renders a row of nav buttons (←back, →forward, ↑up, ⌂home) above the
table. Each button is connected to a dedicated Signal; `PanePresenter` handles them
via the same `PaneViewProtocol` interface, keeping the view passive.
