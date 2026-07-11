# Biome FM

AI-powered cross-platform dual-pane file manager. Python + PySide6/Qt.

## Commands

```bash
# Setup
uv venv .venv --python 3.12
uv pip install -e ".[dev,perf]"

# Tests (TDD — всегда сначала тесты)
uv run pytest tests/ -q                              # все тесты
uv run pytest tests/unit/ -q                          # unit без Qt
uv run pytest tests/integration/ -q                   # с Qt (offscreen)
uv run pytest tests/ -x -v -k "test_specific"        # один тест после фикса

# Lint + type check
uv run ruff check src/ tests/
uv run mypy src/

# Run app
uv run biome-fm

# Package (macOS)
pyinstaller biome-fm.spec
```

## Principles

SOLID / DRY / KISS / TDD. Files < 300 lines (utility/static — no limit). No abstractions "for the future".

**Architecture priorities:** testability (MVP — Presenter тестируется без Qt) → modularity (plugin = 1 файл, pluggy hooks) → maintainability (flat hierarchy, explicit over implicit, TOML config).

**Tests = source of truth.** Critical functionality MUST have unit + integration tests. If tests pass — code works. Every new feature or bugfix → test first (TDD).

## Tech Stack

- **Python 3.12+**, PySide6 (Qt 6.7+), pytest, pytest-qt
- **VFS**: fsspec (local/SSH/S3/archive)
- **Performance**: scandir-rs, xxhash, watchfiles, blake3 (все PyO3/Rust)
- **AI** (optional): anthropic SDK, sentence-transformers, chromadb
- **Plugins**: pluggy + entry_points
- **Config**: TOML (tomllib stdlib)
- **Packaging**: PyInstaller, hatch

## Architecture

```
src/biome_fm/
├── app.py              # QApplication bootstrap, DI wiring
├── config.py           # @dataclass Config + TOML loader
├── session.py          # Tabs, paths, geometry → JSON
├── event_bus.py        # Decoupled events
├── models/             # VFS, FileItem, DirectoryModel(QAbstractTableModel)
├── presenters/         # PanePresenter, ManagerPresenter (MVP — all logic here)
├── views/              # QMainWindow, PaneView, StatusBar (passive, signals only)
├── commands/           # Command ABC + CopyCmd, MoveCmd, DeleteCmd, history
├── operations/         # OpQueue (asyncio + ThreadPool), cancel, progress
├── plugins/            # pluggy hookspecs + entry_points discovery
├── ai/                 # AIProvider protocol, Claude/Ollama/NoOp providers
└── utils/              # platform.py, icons.py
```

**MVP Pattern:** Views emit signals → Presenters react → update Models → push state to Views. Views NEVER import models.

**Command Pattern:** Every file mutation = Command subclass (execute + undo). Non-undoable ops set `undoable=False`.

**VFS:** Protocol class wrapping fsspec. Local = default, archive/SSH/S3 = swap adapter.

**AI:** Provider abstraction. Every feature works without AI (NoOpProvider). Local-first (embeddings), remote for reasoning.

## Testing

```
tests/
├── unit/           # 80% — Presenter + Command + VFS + AI — чистый pytest, БЕЗ Qt
├── integration/    # 15% — pytest-qt + QT_QPA_PLATFORM=offscreen
├── property/       # 5% — Hypothesis: edge cases в путях/именах
└── snapshot/       # Visual regression (screenshot comparison)
```

**Headless:** `QT_QPA_PLATFORM=offscreen` для CI. Linux = xvfb-run.

**Test order:** unit → integration → property → snapshot (unit всегда первые).

**Failed tests — filter first:** `pytest -k "FailedTest"` — никогда не гонять всё ради одного фикса.

## Scratchpad

For tasks with 5+ steps, create `Plans/SCRATCHPAD.md`:
- **Task**: one sentence
- **Plan**: numbered steps
- **Done**: completed steps
- **Current step**: in progress
- **Errors**: unresolved
- Update after EVERY step. Delete when done.

## Agents

`opus`: senior-architect | `sonnet`: senior-developer, code-reviewer | `haiku`: doc-keeper

**Workflow:** `User → senior-architect → senior-developer → code-reviewer → doc-keeper`

## Error Fixing

- Consider multiple causes before deciding
- Make minimal necessary changes
- Run failing test first, then full suite

## Cross-Platform

- `pathlib.Path` everywhere, never hardcode separators
- `QStandardPaths` for app data/config/cache
- `QKeySequence.StandardKey` for Ctrl↔Cmd
- Platform code in `utils/platform.py`, conditional imports
- CI matrix: macOS + Windows + Linux

## Performance

- `setUniformRowHeights(True)` on views
- `fetchMore/canFetchMore` for lazy loading
- `QThread` + worker objects for I/O (signals integrate with Qt event loop)
- `setSortingEnabled(False)` during bulk load
- scandir-rs for 100k+ file traversal
- Signal batching: `beginInsertRows/endInsertRows`, never per-row emit
