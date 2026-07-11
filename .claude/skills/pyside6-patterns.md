---
name: pyside6-patterns
description: "PySide6/Qt patterns — MVP, Model/View, styling, performance, cross-platform."
user-invocable: false
globs:
  - "src/**/*.py"
---

# PySide6 Patterns

## MVP (Model-View-Presenter)

```python
# View — passive, signals only
class PaneView(QWidget):
    path_changed = Signal(Path)
    file_activated = Signal(str)

    def set_file_list(self, items: list[FileItem]):
        self._model.set_items(items)  # push from presenter

# Presenter — all logic, testable without Qt
class PanePresenter:
    def __init__(self, view: PaneView, vfs: VFSProtocol):
        self.view = view
        self.vfs = vfs
        view.file_activated.connect(self._on_activate)

    def navigate(self, path: Path):
        items = self.vfs.listdir(path)
        self.view.set_file_list(items)
```

## Model/View

```python
class DirectoryModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._items: list[FileItem] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            item = self._items[index.row()]
            col = index.column()
            return [item.name, item.size_str, item.date_str][col]

    # Lazy loading
    def canFetchMore(self, parent):
        return self._has_more

    def fetchMore(self, parent):
        batch = self._vfs.fetch_batch(200)
        self.beginInsertRows(parent, len(self._items), len(self._items) + len(batch) - 1)
        self._items.extend(batch)
        self.endInsertRows()
```

## Performance Rules

1. `setUniformRowHeights(True)` on QTreeView/QTableView
2. `setSortingEnabled(False)` during bulk load, re-enable after
3. `beginInsertRows/endInsertRows` for batch insert — NEVER per-row
4. Cache QPixmaps in delegate — never create per-paint
5. `QThread` + worker objects for I/O (signals auto-marshal to main thread)
6. `QTimer.singleShot(0, load)` for deferred startup loading

## Styling

```python
# QSS for theming (load from file)
app.setStyleSheet(Path("resources/dark.qss").read_text())

# Dark mode detection
import darkdetect
theme = "dark" if darkdetect.isDark() else "light"

# Never hardcode colors — use QPalette roles
widget.setAutoFillBackground(True)
```

## Cross-Platform

```python
# Shortcuts: Qt auto-maps Ctrl↔Cmd
QShortcut(QKeySequence.StandardKey.Copy, widget)  # Cmd+C on mac, Ctrl+C elsewhere

# Paths: always QStandardPaths
config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)

# Platform module
IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"
```

## Keyboard (Dual-Pane)

```python
# F-keys as QShortcut
QShortcut(Qt.Key.Key_F5, self, self.copy_files)      # Copy
QShortcut(Qt.Key.Key_F6, self, self.move_files)       # Move
QShortcut(Qt.Key.Key_F7, self, self.mkdir)             # MkDir
QShortcut(Qt.Key.Key_F8, self, self.delete_files)      # Delete

# Tab switches panes
def focusNextPrevChild(self, _next):
    other = self.right_pane if self.left_pane.hasFocus() else self.left_pane
    other.setFocus()
    return True
```

## Context Menus

```python
view.setContextMenuPolicy(Qt.CustomContextMenu)
view.customContextMenuRequested.connect(self._show_context_menu)

def _show_context_menu(self, pos):
    index = self.view.indexAt(pos)
    menu = QMenu(self.view)
    menu.addAction("Copy", self.copy_files)
    menu.addAction("Delete", self.delete_files)
    menu.exec(self.view.viewport().mapToGlobal(pos))
```

## Anti-Patterns

- Business logic in QWidget subclasses (use Presenter)
- `QThread.run()` override (use worker object + moveToThread)
- Hardcoded pixel sizes (use layouts + size policies)
- Per-row signal emission (use begin/end bulk methods)
- `import *` from PySide6 (import specific classes)
