# biome-fm — Dual-Pane File Manager with AI That Actually Operates Files

<p align="center">
  <img src="docs/assets/screenshot.png" alt="biome-fm screenshot" width="800" />
</p>

<p align="center">
  <!-- STATUS -->
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" /></a>
  <a href="https://github.com/german-krasnikov/biome-fm/stargazers"><img src="https://img.shields.io/github/stars/german-krasnikov/biome-fm?style=flat" alt="Stars" /></a>
  <a href="https://github.com/german-krasnikov/biome-fm/commits/main"><img src="https://img.shields.io/github/last-commit/german-krasnikov/biome-fm" alt="Last Commit" /></a>
  <br/>
  <!-- SPEC -->
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/Qt-6.7%2B-41CD52?logo=qt&logoColor=white" alt="Qt 6.7+" />
  <img src="https://img.shields.io/badge/version-0.31.0-informational" alt="v0.31.0" />
  <br/>
  <!-- STACK -->
  <img src="https://img.shields.io/badge/PySide6-GUI-41CD52?logo=qt&logoColor=white" alt="PySide6" />
  <img src="https://img.shields.io/badge/pluggy-plugins-orange" alt="pluggy" />
  <img src="https://img.shields.io/badge/AI-Claude%20%7C%20OpenAI%20%7C%20Ollama-ff6b35" alt="AI backends" />
</p>

> Total Commander-style dual-pane file manager with a built-in AI that reads your filesystem and executes file operations on your behalf — locally, over SFTP, or inside archives.

biome-fm is a keyboard-driven dual-pane file manager built on PySide6. The left pane and the right pane stay in sync while an embedded AI chat watches both. You describe what you want in plain English — the AI calls the same VFS layer the UI uses and does it. No copy-paste of paths, no shell scripting, no context-switching. It runs on macOS, Windows, and Linux, and connects to Claude, OpenAI, and Ollama out of the box.

---

## Why biome-fm?

- **Stop alt-tabbing.** Terminal, diff viewer, hex editor, archive browser, image preview, PDF reader, git-diff — all tabs inside the same window.
- **AI that operates, not just advises.** The chat panel has write access to the VFS. Ask it to reorganize a folder and it executes the moves with undo support.
- **Extensible by design.** pluggy hooks let you add VFS backends, preview renderers, AI providers, and themes as isolated plugins without touching core.
- **Cross-platform, no compromise.** One codebase, native look on macOS, Windows, and Linux. TOML theming with glass effects ships out of the box.

### What you can say

> "Move all PDFs older than 30 days into archive/2024/"

> "Rename these 47 screenshots to kebab-case using their EXIF dates"

> "Find duplicate images in this folder and show me a side-by-side comparison"

> "What changed in this repo since last Tuesday? Show me the diff."

---

## Quick Start

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
uv tool install biome-fm
biome-fm
```

<details>
<summary>Install from source</summary>

```bash
git clone https://github.com/german-krasnikov/biome-fm.git
cd biome-fm
uv sync
uv run biome-fm
```

</details>

<details>
<summary>Compatibility</summary>

| Component | Minimum | Tested |
|-----------|---------|--------|
| Python    | 3.12    | 3.12   |
| PySide6   | 6.7     | 6.8    |
| OS        | macOS, Windows, Linux | macOS |

</details>

<details>
<summary>Development setup</summary>

```bash
uv sync --all-extras
uv run pre-commit install
uv run pytest
```

Optional extras: `ai` (Anthropic + embeddings), `perf` (Rust bindings for speed).

</details>

---

## Features

**File Operations**
- Async copy/move with progress bar + cancel
- Conflict resolution dialog with per-file decisions
- Transfer queue panel (pause, reorder, retry)
- Create/extract archives (zip, tar, encrypted 7z + plugin extensions)
- Checksum dialog (MD5, SHA-256)
- Undo/redo — 50 levels, every mutation is a Command
- Dry-run preview before destructive operations
- Batch execute on selection with template substitution
- Space reclaimer — find and remove large/duplicate files
- Clipboard history ring (last 20 entries)
- `ChownCmd` with full undo support

**UI & Navigation**
- Dual-pane, multi-tab layout with named workspaces
- Breadcrumb bar with drag-and-drop path segments
- Sidebar: volumes, bookmarks, recent locations
- Embedded terminal (Ctrl+`), full-screen subshell toggle (Ctrl+O)
- Inline rename (F2), batch rename with metadata fields (EXIF, MP3 tags)
- Flat/recursive view, TC-style file marks
- OmniBar — unified navigation, command, and search in one input
- Command palette (Ctrl+P) with frecency ranking, F1-F10 action bar
- Gallery view with async thumbnail loading
- Directory comparison panel (side-by-side diff)
- Custom toolbar builder
- Per-directory view state, path autocomplete
- Global UI zoom (Ctrl+=/Ctrl+-), word wrap and text zoom in preview
- Mouse back/forward buttons + trackpad two-finger swipe
- macOS Touch Bar stub
- Session view mode persistence across restarts

**Search & Filter**
- Quick filter with character highlight
- Select by pattern (glob/regex)
- Fuzzy finder (Ctrl+P), virtual search pane
- Reusable search templates
- Advanced filter predicates: `size:>10m mod:today ext:py`
- Spotlight/mdfind scope on macOS

**Preview**
- Syntax-highlighted code and Markdown (Pygments)
- Images, video thumbnails (ffmpeg), audio metadata (mutagen)
- Archive contents, hex dump, git diff, PDF text
- macOS Quick Look fallback, fullscreen viewer (F11)
- Preview cache with 60 s TTL
- Finder Comments + xattr browser in PropertiesDialog

**VFS Backends**
- Local, SFTP/SSH (jump host, tunnel), S3 (with object versioning), WebDAV
- ZIP/TAR/7z/RAR archive browsing
- ISO 9660 and macOS DMG virtual filesystems
- Docker container filesystem browser
- FISH protocol VFS; extfs-style Script VFS (RPM, DEB, ISO)
- rsync backend for delta-transfer; cross-VFS streaming resume
- Plugin-defined custom VFS backends

**Automation & Scripting**
- Python scripting engine (`BiomeContext` + `ScriptingEngine`) — automate any UI action
- Keyboard macro recorder/player with persistent macro store
- Watch rules — auto-actions triggered on folder events
- IPC: Unix socket server + REST API (Bearer token, EventBus dispatch)

**AI Integration**
- Multi-model chat: Claude, OpenAI, Ollama, CLI backends (Claude Code, Codex, OpenCode)
- AI rename suggestions, context-aware file actions
- Natural-language operations (Ctrl+Shift+N)
- AI commit message suggestion from staged diff
- Metadata-based renaming using EXIF/MP3 fields via AI
- AI shell command detection

**Themes & Appearance**
- TOML token-based themes with inheritance
- Color-blind safe theme (Okabe-Ito palette)
- Glass/opacity effect, file-type coloring, active-pane highlight
- Custom column visibility

**Plugins**
- 8 pluggy hookspecs: context menu, custom columns, archive formats, themes, and more
- `entry_points` discovery + local drop-in plugins
- Versioned plugin API
- Plugin-defined custom columns and presigned URL generation

<details>
<summary>Plugin example</summary>

```python
# ~/.config/biome-fm/plugins/my_plugin.py
class Plugin:
    BIOME_FM_API_VERSION = (1, 0)

    def context_menu_actions(self, items, pane_id):
        return [ActionSpec(label="Open in Obsidian", callback=lambda: ...)]
```

Or register via `pyproject.toml`:

```toml
[project.entry-points."biome_fm.plugins"]
my_plugin = "my_plugin:Plugin"
```

</details>

---

## Architecture

<details>
<summary>Source tree</summary>

```
src/biome_fm/
├── models/        # VFS router, FileItem, DirectoryModel
├── presenters/    # Qt-free MVP logic
├── views/         # Passive PySide6 widgets (signals only)
├── commands/      # Command pattern — execute() + undo()
├── operations/    # Async queue (ThreadPool + cancel tokens)
├── preview/       # Provider protocol + renderer registry
├── plugins/       # pluggy hookspecs + entry_point discovery
├── ai/            # AIProvider protocol + concrete providers
├── ipc/           # Unix socket server + REST API (Bearer token)
├── scripting/     # BiomeContext + ScriptingEngine (Python automation)
├── cli/           # CLI installer (configure/doctor)
└── themes/        # TOML color token resolution
```

</details>

**Hybrid Supervising Controller (MVP variant).** Views are passive — they emit signals and render what they're given, holding zero business logic. Presenters subscribe to those signals, run all decisions, and push state back through a typed `Protocol` interface. Every file mutation is a `Command` subclass with `execute()` and `undo()`, stored in a 50-level `CommandHistory`. The VFS layer (`VFSRouter`) dispatches transparently across local paths and archives so presenters never branch on location type.

Full architecture: [`AI/architecture.md`](AI/architecture.md)

---

<!-- CHANGELOG_START -->
## Recent Changes

<details>
<summary><strong>v0.31.0</strong> — 2026-07-21 — Sprint 10: 8 features</summary>

- Session view mode persistence (`PaneSideState.view_mode`), Clipboard History Ring (`ClipboardEntry`, `deque(maxlen=20)`)
- Keyboard Macro Recorder (`MacroRecorder` + `MacroPlayer`, `MacroStore`)
- REST API for Remote Control (`ipc/rest_server.py`, Bearer token, EventBus dispatch)
- Python Scripting Engine (`scripting/` package: `BiomeContext`, `ScriptingEngine`)
- Directory Comparison View (`ComparePanel`), Custom Toolbar Builder (`CustomToolBar`, `ToolbarBuilderDialog`)
- macOS Touch Bar stub (`utils/touch_bar.py`)

</details>

<details>
<summary><strong>v0.30.0</strong> — 2026-07-21 — Sprint 9: 10 features</summary>

- Thumbnail Gallery View (`GalleryView` + `ThumbnailLoader`), Unified Omnibar (`OmniBar`, `OmnibarPresenter`)
- Operation Dry-Run Preview (`DryRunDialog`, `Command.preview()`), Full-screen Subshell Toggle (Ctrl+O)
- Batch Execute on Selection (`BatchExecCmd`), Folder Watch Rules (`WatchRuleEngine`)
- Advanced Filter Bar (`parse_filter` / `FilterSpec`), Multi-Rename Metadata Fields (`[META:key]`, `metadata_reader.py`)
- Smart Space Reclaimer (`SpaceReclaimerPresenter`), External IPC Interface (`ipc/server.py` + `ipc/client.py`)

</details>

<details>
<summary><strong>v0.29.0</strong> — 2026-07-21 — Sprint 8: remote VFS + Docker</summary>

- SSH jump host / tunnel, remote file search (server-side find), cross-VFS streaming resume
- FISH protocol VFS, extfs-style Script VFS (RPM/DEB/ISO), ISO 9660 + macOS DMG VFS
- Docker container filesystem browser, rsync backend for delta-transfer
- S3 object versioning browser, plugin-defined custom columns

</details>

<details>
<summary><strong>v0.28.0</strong> — 2026-07-21 — Sprint 7: 12 features</summary>

- Color-blind safe theme (Okabe-Ito palette), `ChownCmd` with undo, file selection export to clipboard
- Preview cache 60 s TTL; Finder Comments + xattr browser in PropertiesDialog
- AI commit message suggestion in `GitCommitDialog` via `staged_diff()` + AI provider
- Shell env vars `BIOME_CWD`/`BIOME_SELECTED`/`BIOME_CURSOR` injected into terminal on launch
- Spotlight/mdfind search scope, dependency cleanup scanner, presigned URL generation, macOS Share Sheet

</details>

<details>
<summary><strong>v0.27.0</strong> — 2026-07-21 — Sprint 6: 18 quick-win features</summary>

- Natural sort, symlink target column, Unicode NFC normalization in file listing
- Mouse back/forward buttons + trackpad two-finger swipe in pane navigation
- Word wrap toggle, text zoom (Ctrl+Wheel), tail mode, fit-to-window image in preview
- Global UI zoom (Ctrl+=/Ctrl+-/Ctrl+0), command palette frecency ranking
- Encrypted 7z creation, macOS quarantine manager, remote timestamp preservation

</details>

Full history: [CHANGELOG.md](CHANGELOG.md)
<!-- CHANGELOG_END -->

---

## Documentation

| Resource | Description |
|----------|-------------|
| [`AI/architecture.md`](AI/architecture.md) | Technical architecture, VFS router, MVP pattern, threading model |
| [`docs/`](docs/) | User-facing guides: keyboard shortcuts, plugin authoring, AI setup |
| [`.claude/skills/`](.claude/skills/) | Development patterns for contributors (PySide6, TDD, VFS) |
| [`CHANGELOG.md`](CHANGELOG.md) | Full release history |

---

## FAQ

<details>
<summary>Is this Total Commander for Mac?</summary>

Inspired by Total Commander and Midnight Commander — dual-pane, keyboard-driven, archive browsing. The difference: native cross-platform look via PySide6 and an optional AI layer for rename suggestions, natural-language ops, and file summaries.

</details>

<details>
<summary>Does it work without AI / an API key?</summary>

Yes. The default provider is `NoOpProvider` — all AI features are hidden when no provider is configured. Everything else works fully offline.

</details>

<details>
<summary>Can I write plugins?</summary>

Yes. biome-fm uses [pluggy](https://pluggy.readthedocs.io/) hooks. Drop a `.py` file in `~/.config/biome-fm/plugins/` or register via `entry_points` in your package. See `docs/` for a walkthrough.

</details>

<details>
<summary>How does it handle 100k+ files?</summary>

Directory scanning uses `scandir-rs` (Rust) with a Python fallback. The file list uses `QAbstractItemModel` with lazy loading and uniform row heights — Qt never measures rows it hasn't painted.

</details>

---

## Contributing

Bug reports and PRs welcome. Please open an issue before large changes. See [`CLAUDE.md`](CLAUDE.md) for the dev workflow and agent conventions.

---

## License

[MIT](LICENSE) — Built by [German Krasnikov](https://github.com/german-krasnikov)
