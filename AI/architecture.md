# Biome FM Architecture

## Overview

```
src/biome_fm/
├── app.py              # QApplication bootstrap, DI wiring
├── qt.py               # Centralized PySide6 imports (Anki pattern)
├── config.py           # @dataclass Config + TOML loader
├── session.py          # Tabs, paths, geometry → JSON persistence
├── event_bus.py        # Decoupled pub/sub events
│
├── models/
│   ├── file_item.py    # FileItem frozen dataclass
│   ├── vfs.py          # VFSProtocol + LocalVFS
│   └── directory_model.py  # QAbstractTableModel for file lists
│
├── presenters/
│   ├── pane_presenter.py     # Drives one pane (cd, select, sort)
│   ├── manager_presenter.py  # Owns panes, tabs, inter-pane ops
│   └── operation_presenter.py # Progress, cancel, conflict resolution
│
├── views/
│   ├── main_window.py   # QMainWindow shell
│   ├── pane_view.py     # QTableView + path bar + filter
│   ├── progress_view.py # Embedded progress (not modal)
│   └── status_bar.py    # Selection info, free space
│
├── commands/
│   ├── base.py          # Command ABC + CommandHistory
│   ├── copy_cmd.py      # CopyCommand (shutil.copy2)
│   ├── move_cmd.py      # MoveCommand
│   ├── delete_cmd.py    # DeleteCommand (send2trash)
│   ├── rename_cmd.py    # RenameCommand
│   └── mkdir_cmd.py     # MkdirCommand
│
├── operations/
│   ├── queue.py         # OpQueue: asyncio + ThreadPoolExecutor
│   ├── task.py          # OpTask: priority, cancel, progress
│   └── conflict.py      # ConflictPolicy + resolver
│
├── plugins/
│   ├── hookspecs.py     # pluggy @hookspec definitions
│   ├── manager.py       # PluginManager: entry_points discovery
│   └── builtin/
│       ├── archive.py   # ZIP/TAR as VFS (fsspec zip://)
│       └── preview.py   # Quick-look panel
│
├── ai/
│   ├── provider.py      # AIProvider Protocol + NoOp/Claude/Ollama
│   ├── search.py        # Semantic file search (sentence-transformers)
│   └── commands.py      # AI-powered batch rename, NL ops
│
└── utils/
    ├── platform.py      # IS_MAC/IS_WIN/IS_LINUX, OS helpers
    ├── icons.py         # QFileIconProvider + caching
    └── sanitize.py      # Filename sanitization (cross-platform)
```

## Patterns

### MVP
Views emit signals → Presenters react → update Models → push to Views.
Views NEVER import models. Presenters testable without Qt.

### Command + Undo
Every file mutation = Command(execute + undo). CommandHistory (50 levels).

### VFS Host Chaining (from Nimble Commander)
`VFS(parent=outer_vfs, junction="/archive.zip")` — archives inside SSH.

### Plugin Hooks (pluggy)
`fm_register_opener`, `fm_context_menu_items`, `fm_preview_panel`.
Discovery via `importlib.metadata.entry_points(group="biome_fm.plugins")`.
