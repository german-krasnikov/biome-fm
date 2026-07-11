# Biome FM Architecture

## Overview

```
src/biome_fm/
├── __main__.py         # CLI entry point: QApplication bootstrap, apply_theme, create_app()
├── app.py              # create_app() factory — full DI wiring (VFSRouter, Config,
│                       #   Session, Plugins, AI, CommandPalette, PaneSideViews)
├── qt.py               # Centralised PySide6 imports (Anki pattern)
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
│   ├── pane_presenter.py     # Drives one pane (cd, select, sort, current_item)
│   ├── tabs_presenter.py     # Owns N PanePresenters per side; current_item delegation
│   ├── manager_presenter.py  # Inter-pane ops (copy, move, delete target selection)
│   ├── ai_presenter.py       # AI chat bridge (AIProvider ↔ AIChatViewProtocol)
│   ├── compare_presenter.py  # Directory diff (left vs right pane)
│   ├── rename_presenter.py   # Multi-rename (pattern, counter, ext substitution)
│   └── search_presenter.py   # File search (name glob + content grep)
│
├── views/
│   ├── main_window.py    # QMainWindow: splitter, AI panel toggle, closeEvent,
│   │                     #   splitter_sizes persistence
│   ├── pane_side_view.py # QTabBar + QStackedWidget — tabbed pane container
│   ├── pane_view.py      # Passive QWidget: path bar + QTableView + filter
│   ├── ai_chat_panel.py  # Passive AI chat (message_submitted Signal)
│   ├── action_bar.py     # F1-F10 function key bar
│   ├── command_palette.py # Fuzzy-search command launcher
│   └── theme.py          # Dark/light palette + stylesheet
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
