# Changelog

All notable changes to Biome FM are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.26.0] — 2026-07-18

### Added

**Sessions & Workspaces**
- Named sessions — save and restore full left+right pane layout by name (`models/session_store.py`, `views/session_picker_dialog.py`)

**Task Runner**
- Makefile/Justfile target runner — detects Make and Just targets in the active directory, runs with live QProcess output (`views/task_runner_dialog.py`, `models/project_detector.parse_makefile_targets`, `parse_justfile_targets`)

**Shell & Navigation**
- Path completion — `path_completions(text)` in `utils/path_completion.py` provides glob-based completions for absolute, tilde, and relative paths in the command bar

**Cloud**
- `CloudConnectionStore` — JSON-backed list of cloud connection URLs (`models/cloud_connection_store.py`)

**VFS Plugin Hook**
- `provide_vfs` hookspec (firstresult) — plugins can now supply a custom VFS implementation for any path prefix (`plugins/hookspecs.py`)

### Tests
- 1921 unit tests, 532 integration tests (2453 total)

---

## [v0.25.0] — 2026-07-18

### Added

**Disk Analysis**
- Storage treemap — squarify-based disk usage visualization; background scanner + QPainter widget; click to navigate (`presenters/treemap_presenter.py`, `views/treemap_panel.py`)
- Large file finder — configurable min-size threshold; background `os.walk` scan; sortable table (`views/large_file_dialog.py`)

**Accessibility**
- High Contrast theme — `themes/high-contrast.toml`; inherits dark with `#FFFF00` accent and `#00FFFF` accent2; `#FFFFFF` borders on `#000000` base

**Desktop Integration**
- Global hotkey — `register_global_hotkey(key_combo, callback)` via pynput (optional dep); returns listener handle or None if unavailable (`utils/global_hotkey.py`)
- macOS Automator Quick Action — `install_quick_action()` installs "Open in Biome FM" workflow to `~/Library/Services/` (`cli/automator.py`); `biome-fm install-service` CLI subcommand

---

## [v0.24.0] — 2026-07-18

### Added

**Tags**
- `TagCmd` — batch tag assign/remove command with undo; saves previous tag state per path for undo (`commands/tag_cmd.py`)

**Git**
- Git virtual pane — `git_changed_files(repo, cache)` returns `list[FileItem]` for all dirty paths in a repo; navigate to a virtual pane of uncommitted changes (`git/virtual_pane.py`)
- Git worktree navigator — `list_worktrees(repo)` parses `git worktree list --porcelain`; returns `[{path, head, branch}]` dicts; timeout-safe (`git/worktree_ops.py`)

**Editor**
- Pygments syntax highlighter — `PygmentsHighlighter` (QSyntaxHighlighter); theme-aware (light/dark token colors); skips TextLexer; plugs into `EditorDialog` (`views/editor_highlighter.py`)

**File List**
- Group header delegate — `GroupDelegate` draws an accent separator line + group label above the first row of each group in the file list; reads `GROUP_ROLE` from proxy (`views/group_delegate.py`)

### Tests
- 41 new tests covering git virtual pane, worktree ops, tag command, group delegate

---

## [v0.23.0] — 2026-07-18

### Added

**Remote / Cloud VFS**
- `RcloneVFS` — VFS backed by `rclone lsjson` subprocess; supports `listdir`, `stat`, `copy`, `move`, `delete`, `mkdir`; nanosecond modtime parsing (`models/rclone_vfs.py`)
- `RemoteListCache` — thread-safe TTL=30s listing cache for remote VFS operations (`models/remote_cache.py`)
- `PreviewFileCache` — SHA1-keyed local temp-file cache for remote file preview; 50 MB max, LRU eviction (`models/preview_file_cache.py`)

**Credentials & Profiles**
- `CredentialStore` — `get_credential` / `set_credential` / `delete_credential` via keyring; in-process dict fallback when keyring unavailable (`models/credential_store.py`)
- `CloudProfileStore` + `CloudProfile` — TOML-backed CRUD store for named cloud connections (s3/sftp/ftp/ftps/webdav/rclone) with host, port, user, bucket (`models/cloud_profile_store.py`)
- `CloudProfileDialog` — CRUD dialog: list on left, edit form on right (`views/cloud_profile_dialog.py`)
- `QuickConnectBar` — URI QComboBox + Connect button widget; emits `connect_requested(uri)` (`views/quick_connect_bar.py`)
- `UploadQueuePanel` — passive view showing pending/active/done uploads with per-item progress (`views/upload_queue_panel.py`)

**Remote Editing**
- `RemoteEditCmd` — download remote file → open `$EDITOR` → re-upload if mtime changed; not undoable (`commands/remote_edit_cmd.py`)

**Events**
- `RemoteConnected(scheme, host)` — fired when a remote VFS connects
- `RemoteDisconnected(scheme, host)` — fired on disconnect
- `RemoteSyncing(scheme, host, active)` — fired while remote I/O in progress

### Tests
- 72 new tests covering RcloneVFS, RemoteListCache, PreviewFileCache, CredentialStore, CloudProfileStore, RemoteEditCmd

---

## [v0.22.0] — 2026-07-18

### Added

**File Operations**
- `CopyMoveDialog` — TC-style copy/move destination dialog with editable path, recent-history QComboBox, and browse button (`views/copy_move_dialog.py`)
- `PermissionsEditorDialog` — bulk chmod dialog with 9 bit-checkboxes (rwxrwxrwx); shows common mode for mixed selections; POSIX-only (`views/permissions_editor_dialog.py`)
- `ChmodCmd` — batch `os.chmod` command with undo; saves previous mode per path; supports optional `vfs.chmod` for remote VFS (`commands/chmod_cmd.py`)

**Selection**
- `SelectCriteria` + `SelectByAttrDialog` — pure-Python predicate (name glob, extensions list, min/max size bytes, min/max age days); `matches(item)` method; dialog builds criteria from user input (`models/select_criteria.py`, `views/select_criteria_dialog.py`)
- `FileCollector` — deduplicated multi-directory virtual panel; `add(items)` / `remove(paths)` / `items()` / `count()` / `clear()`; show via `navigate_virtual` (`presenters/file_collector.py`)

**Navigation**
- `QuickCDDialog` — frecency + live filesystem-path-completion quick-change-directory; `Alt+C` shortcut; `path_selected` Signal (`views/quick_cd_dialog.py`)

**Leader Key**
- `WhichKeyPopup` — floating monospace hint overlay (ToolTip window type) showing available next keys in a leader sequence (`views/which_key_popup.py`)
- `LeaderFilter` — QApplication event filter for leader key sequences; ignores input fields; 300ms timeout; emits `action_triggered(str)` (`views/leader_filter.py`)

**User Menu**
- `UserMenuItem` + `load_user_menu(cwd)` — walks up from `cwd` for `.biome-menu.toml`; falls back to global config; per-directory contextual menu items with shortcut field (`models/user_menu.py`)

### Tests
- 104 new tests covering FileCollector, SelectCriteria, CopyMoveDialog, ChmodCmd, QuickCDDialog, WhichKeyPopup, LeaderFilter

---

## [v0.21.0] — 2026-07-18

### Added

**Search**
- Exclusion patterns (`-pattern` prefix) in search queries
- Case-sensitive and whole-word match toggles
- Multi-pattern AND search (space-separated terms all must match)
- Context lines: show N lines before/after each match (like `grep -C`)
- Archive content search: search inside zip/tar/7z members
- Search scope selector: current directory, subtree, or all open tabs

**Sync**
- Dry-run preview mode: shows what would change before executing
- Mirror mode: delete destination files not present in source
- Exclude-pattern list: skip files by glob during sync
- Conflict detection with per-file Overwrite / Skip / Auto-Rename resolution
- Session profiles: save and reload sync configurations (`SyncProfiles`)

**Git**
- Branch switcher dialog: list, checkout, and create branches in-app (`git/branch_ops.py`)
- In-app commit dialog: stage files, write message, push (`git/commit_ops.py`)
- Conflict navigator: step through merge conflicts with inline accept/reject (`git/conflict_ops.py`)

**Preview**
- `.env` files: secret values masked (`***`) by default; click to reveal (`preview/providers/dotenv.py`)
- CSV: rendered as sortable HTML table with column headers (`preview/providers/csv_preview.py`)
- JSON / XML: collapsible tree view (`preview/providers/json_tree.py`)
- Jupyter notebooks: cells rendered with code and outputs (`preview/providers/notebook.py`)
- Office documents (`.docx` / `.xlsx` / `.pptx`): text extraction preview (`preview/providers/office.py`)

**Navigation**
- URI navigation in breadcrumb: type `sftp://user@host/path` or `s3://bucket/key` to navigate (`uri_parser.py`)
- Numbered bookmarks: `Ctrl+1`–`Ctrl+9` jump to slot; `Alt+Ctrl+1`–`9` assign current path
- Hotlist (`Ctrl+D`): TC-style persistent path shortcuts (`presenters/hotlist.py`)
- Path yank leader sequences: `y n` (name), `y p` (full path), `y d` (directory), `y e` (extension)
- Quick view (`Ctrl+Q`): inline preview overlay without opening the preview pane (`quick_view_state.py`)
- Drive bar `Alt+F1` / `Alt+F2`: volume picker for left / right pane (`presenters/drive_list.py`)

**Developer**
- Project action bar: detected project type (Python/Node/Rust/…) shows contextual actions (`project_actions.py`)
- Panelize: pipe any shell command's stdout into the active pane as a virtual file list (`utils/panelize.py`)
- Leader key sequences: multi-key bindings configurable per-user (`presenters/leader_handler.py`)

**Configuration**
- Config backup: 7 rolling backups on every save (`~/.config/biome-fm/config.toml.bak.N`)
- External diff tool: `Config.diff_tool` — command invoked by the Diff dialog instead of the built-in viewer
- Opener rules TOML: `~/.config/biome-fm/opener_rules.toml` — glob → command mapping with priority (`models/opener_rules.py`)
- Column visibility: hide/show Name/Size/Modified/Ext/Git per-pane; persisted in config (`presenters/column_state.py`)

**Archives**
- 7z and RAR read support via `py7zr` / `rarfile` (`models/archive_7z.py`)
- fsspec-backed VFS: browse S3 (`s3://`), FTP (`ftp://`), WebDAV (`webdav://`) as local directories (`models/fsspec_vfs.py`)

**AI**
- Semantic search: natural-language query over file-index (`presenters/semantic_search.py`)
- Group rename: AI suggests cohesive filenames for a multi-file selection (`presenters/ai_group_rename.py`)
- Diff summary: one-sentence AI description of uncommitted git changes on the focused file (`presenters/ai_diff_summary.py`)
- Predictive destination: AI pre-fills the copy/move target path based on recent usage (`presenters/predictive_dest.py`)

**Advanced**
- Multi-file find & replace: regex replace across all marked files with per-file preview (`commands/editor_rename_cmd.py`)
- Selective copy by mask: copy only files matching a glob from the current selection (`presenters/copy_filter.py`)
- Rename templates: `{date}`, `{name}`, `{ext}`, `{n}`, `{parent}` placeholders in batch rename (`presenters/rename_template.py`)
- Miller columns: optional third column shows contents of focused directory's first child (`presenters/miller_state.py`)
- Cross-directory marks: marks persist across directory changes; `Ctrl+Shift+M` opens marked list (`presenters/cross_marks.py`)

## [v0.20.0] — 2026-07-17

### Added
- **Preview Script Providers** — drop a `.toml` file in `~/.config/biome-fm/preview_scripts/` to add a custom preview renderer for any file extension (`ScriptSpec` / `ScriptPreviewProvider` / `load_script_providers`)
- **Custom File Associations** — JSON-backed suffix→app mapping (`FileAssociations`); edit via `~/.config/biome-fm/associations.json`
- **User Actions / Context Menu** — define shell commands that appear in the right-click menu (`UserActionsStore`, `UserAction`); edit via Tools → Menu Builder dialog
- **Script Runner** — run `.py` and `.sh` scripts from a user directory with `BIOME_SELECTED` / `BIOME_CWD` env vars injected (`ScriptRunner`)
- **Git preview modes** — Log and Blame buttons in the preview panel route to `GitLogPreviewProvider` / `GitBlamePreviewProvider`; shows last-50 commits and per-line authorship
- **SQLite preview** — `SqlitePreviewProvider` renders `.db`/`.sqlite`/`.sqlite3` tables (up to 5 tables × 20 rows) as HTML
- **Built-in text editor** — `EditorDialog` + `EditorPresenter`; `F4` opens the cursor file; `Ctrl+S` saves; unsaved-changes guard on close
- **Frecency-based jump dialog** — `FrecencyStore` tracks directory visits; `Ctrl+J` opens `JumpDialog` sorted by frecency score
- **Clipboard cut/copy/paste** — `ClipboardService` (Qt-free); `Ctrl+X/C/V` wired in `app.py`; cut items shown dimmed in the file list
- **Trash** — `TrashCmd` wraps `send2trash`; `Delete` key moves selection to OS trash
- **Zoomable image viewer** — `ZoomableImageWidget` in preview panel; `Ctrl+Wheel` zooms, `R` rotates 90°
- **Spring-loaded folders** — hovering DnD payload over a folder for 800ms auto-expands it
- **Persistent marks** — marked files survive navigation within the same pane; restored on back-navigate
- **Per-directory view state** — `DirStateStore` remembers sort column/order and filter per directory (LRU-500, JSON persistence)
- **Git status in status bar** — `GitStatusCache` + `GitStatusWorker` (ThreadPoolExecutor, 10s TTL) push XY codes to the status bar as colored badges
- **Volume watcher** — `VolumeWatcher` polls OS every 3s; `volume_added`/`volume_removed` Signals update the sidebar
- **File indexer** — `FileIndexer` uses SQLite FTS5 for background full-directory indexing; `search(query)` → list[Path]
- **Project detector** — `detect_project(path)` walks up looking for `pyproject.toml`, `package.json`, `Cargo.toml`, etc.
- **Tab groups** — `TabGroupStore` saves/restores named tab-set snapshots (JSON)
- **File templates** — `TemplateStore` with builtin Python/Markdown/Text templates used by `NewFileCmd`
- **Keyboard shortcut store** — `ShortcutStore` (JSON) + `ShortcutHelpDialog` cheatsheet (28 bindings); `F1` / `?` to open
- **Gitignore filter** — `GitignoreFilter.is_ignored(path)` via `git check-ignore -q`
- **Encoding detection** — `utils/encoding.py`: `detect_encoding` (chardet if available) + `decode_smart`
- **Panelize** — `parse_shell_output(stdout, cwd)` → `list[FileItem]`; pipe any shell command into the pane
- **Swap panes** — `ManagerPresenter.swap_panes()` exchanges left/right paths + histories; `Ctrl+U`
- **Move tab to other pane** — `ManagerPresenter.move_tab_to_other_pane(tab_idx)`
- **Content diff / compare** — `ComparePresenter.content_diff` → unified diff string; `content_compare` → bool
- **SFTP VFS** — `SFTPVfs` (paramiko); `parse_sftp_uri()` / `SFTPConnectDialog`; full connect/ls/read/stat
- **Open With dialog** — `OpenWithDialog` lists discovered apps + custom command field; `app_selected` Signal
- **Properties dialog** — `PropertiesDialog` shows General + Permissions (9-bit checkboxes) tabs
- **Diff view dialog** — `DiffViewDialog` renders unified diff with Pygments syntax highlight
- **Directory tree panel** — `DirTreePanel` (QFileSystemModel, dirs only); `path_selected` Signal
- **Disk usage widget** — `DiskUsageWidget` (compact progress bar, 120px); shows free GB in tooltip
- **Op log panel** — `OpLogPanel` + `OpLogModel` live table of file operations (Time/Op/Status/Details; max 500)
- **Info panel** — `InfoPanel` + `InfoPresenter` sidebar: name/size/mtime/permissions/MIME per cursor file
- **Menu builder dialog** — `MenuBuilderDialog` GUI for editing `UserActionsStore`
- **Archive format dialog** — `ArchiveFormatDialog` for choosing name + format (zip/tar.gz/tar.bz2)
- **Git stash dialog** — `GitStashDialog` (passive view); apply/pop/drop/new stash operations
- **Config bundle** — `config_bundle.export_config` / `import_config`; TOML import validates field names
- **App chooser** — `discover_apps()` cross-platform (macOS: mdfind, XDG: .desktop, Windows: stub)
- **FAYT bar** — `FAYTBar` with mode prefixes (`/` navigate, `:` command, `?` search)
- **Deferred tab loading** — `TabsPresenter` restores session tab paths lazily on first activation
- **Layout profiles** — `Config.layout_profiles` dict stores named splitter layouts; `save_layout_profile` / `load_layout_profile`
- **Follow system theme** — `Config.follow_system_theme`; `Config.editor_cmd` for external editor preference
- **Virtual scroll** — `DirectoryModel.canFetchMore` / `fetchMore` for large directories
- **New commands**: `NewFileCmd`, `SymlinkCmd`, `HardlinkCmd`, `EditorRenameCmd` ($EDITOR bulk rename), `ExportListingCmd` (txt/csv), `TrashCmd`
- **New keyboard shortcuts** (feat/48-killer-features branch):
  - `Delete` — move selected to trash
  - `Shift+Delete` — permanently delete selected
  - `Ctrl+C` / `Ctrl+X` / `Ctrl+V` — clipboard copy / cut / paste
  - `Ctrl+U` — swap panes
  - `Ctrl+J` — frecency jump dialog (recent directories)
  - `F4` — open file in editor
  - `F1` / `?` — shortcut help dialog
  - `Ctrl+S` — save in built-in editor
  - `R` — rotate image in preview
  - `Ctrl+Wheel` — zoom in image preview
  - `Insert` — mark without advancing cursor

## [v0.19.1] — 2026-07-17

### Removed
- **MCP server** — `src/biome_fm/mcp/` (server.py, _entry.py, tools/) deleted entirely;
  the `biome-fm-mcp` entry point and `mcp` optional dependency removed from `pyproject.toml`;
  all MCP server unit tests removed (`tests/unit/mcp/`)
- **Renamed `mcp/` → `cli/`** — the CLI installer subcommands (configure/doctor/version/uninstall)
  were kept intact; module is now `src/biome_fm/cli/`

### Changed
- **`merger.py` function names** — `merge_mcp_config` → `merge_config`, `remove_mcp_entry` →
  `remove_entry`, `merge_toml_mcp` → `merge_toml_config`, `remove_toml_mcp_entry` →
  `remove_toml_entry` (generic names now that MCP is gone)
- **`__version__`** uses `importlib.metadata.version("biome-fm")` instead of a hardcoded string

## [v0.19.0] — 2026-07-17

### Fixed
- **`preserve_scroll` always True** — `PanePresenter._navigate_no_history` now passes `preserve_scroll`
  only when staying in the same directory; navigating to a new path resets scroll to top
- **Archive crash on .tar.bz2 / .tar.xz** — `_is_tar()` in `archive_vfs.py` now recognises all
  compound `.tar.*` extensions, not just `.tar.gz`
- **Dual EventBus singleton** — `app.py` was constructing two `EventBus` instances; unified to one
- **Progress dialog showed no progress** — callback now correctly forwards `(current, total)` pairs
  from `ProgressCopyCmd` / `ProgressMoveCmd` to the dialog
- **MCP server unrestricted by default** — `mcp/_entry.py` now sets `allowed_roots` to the user home
  directory when no explicit roots are configured, preventing accidental full-filesystem exposure
- **Chat log ignores system theme** — `_chat_log.py` bubble colours now react to Qt palette so they
  look correct in both dark and light themes
- **Dead `customContextMenuRequested` connection** — stale signal wiring in `main_window.py` removed
- **TabsPresenter missing delegations** — `close_tab`, `rename_tab`, `reorder_tabs` were not
  forwarded to the underlying model; all three now properly delegated
- **Bookmark write data loss** — `BookmarkStore._save()` now writes atomically (temp file + replace)
  and deep-copies the node tree before serialising to prevent mutation mid-write
- **`parse_codex_line` multi-block** — parser now accumulates across continuation lines correctly
  instead of emitting partial fragments

### Added
- **`SearchCoordinator`** — extracted from `app.py`; owns the search dialog / results panel lifecycle
  and wires `SearchPresenter`; `presenters/search_coordinator.py`
- **`dnd_utils.py`** — `make_path_mime()` DRY helper moved from `pane_view.py` to
  `views/dnd_utils.py` so breadcrumb bar and pane view share one implementation
- **`_panel_buttons.py`** — `add_panel_buttons()` factory extracted from `ai_chat_panel.py` /
  `preview_panel.py` into `views/_panel_buttons.py`; panels share one button builder
- **`markdown_renderer` in `preview/`** — `models/markdown_renderer.py` relocated to
  `preview/markdown_renderer.py` (single owner; models layer no longer imports Qt rendering code)
- **`_DARK_FALLBACK` in `plugins/types.py`** — moved from `plugins/builtin/dark_theme.py` so all
  plugins can reference the canonical fallback token dict without a circular import
- **`supports_events` on `AIProviderProtocol`** — boolean property; CLI providers return `True`,
  API providers return `False`; lets callers skip `chat_stream_events()` without duck-typing
- **`_proc_ctx()` helper in `CliProvider`** — DRY context manager wraps `Popen` setup / teardown
- **`_file_text()` helper in `archive_vfs`** — single reader for member text extraction
- **`_child_of()` helper in `archive_vfs`** — replaces repeated `Path.is_relative_to()` guard
- **`_glass_alphas()` helper in `theme.py`** — computes all three alpha values from one opacity %
- **EventBus error isolation** — uncaught exceptions in subscribers are caught and logged; one bad
  handler no longer silences the remaining subscribers on the same event
- **Preview cache thread-safety** — `PreviewPresenter._cache` access now guarded by `threading.Lock`
- **PaneView cursor-row cache** — `_cursor_row` cached on selection change; `_DropHintDelegate.paint`
  reads cache instead of re-querying `currentIndex()` on every cell repaint
- **Plugin file-operation hooks** — `ManagerPresenter` now calls `before_file_operation` (veto) and
  `on_file_operation` (notification) hooks for copy / move / delete via the plugin manager

### Features (48 killer features — `feat/48-killer-features`)

**File Operations**
- **Conflict resolution dialog** — per-file or bulk Overwrite / Skip / Auto-Rename choices during copy/move; `ConflictResolver` thread-safe rendezvous; `views/conflict_dialog.py`
- **Transfer queue panel** — live progress panel for all active copy/move operations; `views/transfer_queue_panel.py`
- **Archive create/extract** — right-click → Archive Selected; Extract Here; `ArchiveCmd` + `ExtractCmd` in `commands/archive_cmd.py`
- **Checksum dialog** — MD5 / SHA1 / SHA256 for selected files; `views/checksum_dialog.py`, `commands/checksum_cmd.py`

**UI & Navigation**
- **Embedded terminal panel** — `Ctrl+`` ` toggles a `QProcess`-backed shell panel; `views/terminal_panel.py`
- **Sidebar panel** — collapsible panel showing volumes, bookmarks, and recent dirs; `views/sidebar_panel.py`
- **Flat view** — recursive file listing mode (all descendants in one view)
- **Inline rename** — `F2` / `F9` triggers in-place name editing in the table
- **Batch rename dialog** — pattern/counter/regex rename with live preview; `views/batch_rename_dialog.py`
- **Named workspaces** — save/restore left+right path sets; `models/workspace_store.py`, `views/workspace_dialog.py`
- **Per-directory view state** — sort column and filter persist per visited directory; `models/view_state.py`
- **Path autocomplete** — breadcrumb edit mode shows filesystem completions

**Search & Filter**
- **Search templates** — save/load named search patterns; `models/search_template_store.py`
- **Select by pattern** — glob-based multi-select dialog; `views/pattern_dialog.py`
- **Fuzzy finder** — `Ctrl+P` popup file search with difflib scoring; `views/fuzzy_finder.py`, `presenters/fuzzy_presenter.py`
- **Quick filter char highlight** — matched characters underlined in the file list (feat #45)
- **Virtual / search pane** — search results shown as a virtual pane (no navigation needed)

**AI Integration**
- **AI rename suggestions** — AI suggests better filenames with per-file accept/skip; `presenters/ai_rename_presenter.py`, `views/ai_rename_dialog.py`
- **AI context-aware actions** — builtin extension→action map + AI suggestions for selected file; `ai/context_actions.py`, `views/ai_context_dialog.py`
- **Natural language operations** — type "move all PDFs to docs/" and AI parses it to a file op; `presenters/nl_ops_presenter.py`, `views/nl_ops_dialog.py` (`Ctrl+Shift+N`)
- **AI shell command detection** — `AIPresenter.drain()` detects shell blocks in AI responses; `AIChatPanel.show_shell_ops()` offers one-click execution

**Preview**
- **Video thumbnail preview** — `VideoPreviewProvider` calls ffmpeg to grab frame 1s; priority 7
- **Archive preview** — lists zip/tar contents as HTML; `ArchivePreviewProvider`, priority 6
- **Hex dump preview** — 4 KB dump for binary files; `HexPreviewProvider`, priority 9
- **Audio metadata preview** — title/artist/album via mutagen (optional); `MetadataPreviewProvider`, priority 7
- **Git diff preview** — colored diff for dirty/staged files; `GitDiffPreviewProvider`, priority 3
- **PDF preview** — text extraction; `PDFPreviewProvider`, priority 4
- **macOS Quick Look fallback** — `QuickLookProvider` (macOS-only), priority 990
- **Fullscreen viewer** — `F11` or double-click → `FullscreenViewer`; `views/fullscreen_viewer.py`

**File Metadata**
- **File tags** — assign colored tags per file; TOML persistence; `models/tag_store.py`, `views/tag_dialog.py`
- **macOS Finder tags** — show Finder tag color dots in file list; `models/finder_tags.py` (xattr/ctypes, macOS-only)
- **File highlighting rules** — glob+color rules dim/highlight files by pattern; `models/highlight_rules.py`, `views/highlight_rules_dialog.py`
- **Custom column visibility** — hide Size/Modified/Ext columns; persisted in `hidden_columns` config; `Ctrl+Shift+Y` opens settings

**Directory Operations**
- **Synchronize directories** — compare left↔right panes, choose direction, sync; `presenters/sync_presenter.py`, `views/sync_dialog.py` (`Ctrl+Shift+Y`)
- **Duplicate file finder** — content-hash scan, shows groups, delete selected; `presenters/duplicate_presenter.py`, `views/duplicate_panel.py`
- **Directory size calculator** — background `calc_tree_size()` with cancel; `utils/dir_size.py`
- **Temp file panel** — browse/delete platform temp files older than N days; `views/temp_panel.py`

**Git Integration**
- **Git status column** — git XY status shown inline; `git/status_cache.py` (TTL=10s), `git/worker.py`
- **Git stage command** — stage/unstage files from the file list; `commands/git_stage.py`
- **Git diff preview** — see above

**VFS / Backend**
- **SFTP VFS stub** — `parse_sftp_uri()` + `SFTPVfs` (requires paramiko, stub for future); `models/sftp_vfs.py`
- **Filesystem watcher** — watchfiles-backed debounced refresh; `utils/watcher.py`

**Settings**
- **`show_git_status`** — `bool = True`; toggles git status column (General tab)
- **`auto_preview`** — `bool = True`; auto-opens preview on cursor move (General tab)
- **`highlight_rules`** — `list[dict]`; glob+color highlight rules (Appearance tab)
- **`hidden_columns`** — `list[str]`; persisted column visibility

**Utilities**
- **Shell variable expansion** — `expand_shell_vars()` TC-style `$F $f $d $t $n $e`; `utils/shell_vars.py`
- **User command store** — TOML-backed user-defined shell commands with shortcuts; `models/command_store.py`

### Removed
- **`make_provider()` factory** — replaced by `make_providers()` (plural); dead single-provider
  factory removed from `ai/__init__.py`
- **Dead config fields** — `Config.ai_api_key`, `Config.ai_model`, and unused toggle wrapper fields
  removed; per-provider model fields remain
- **`_home()` helper on `PanePresenter`** — inlined; was a one-liner wrapping `Path.home()`
- **Qt imports from `plugins/manager.py`** — plugin manager is now pure Python; Qt-dependent plugin
  helpers moved to the views layer

### Tests
- `tests/unit/test_archive_is_tar.py` — `_is_tar` with .tar.bz2/.tar.xz (new)
- `tests/unit/test_archive_child_of.py` — `_child_of` helper (new)
- `tests/unit/test_event_bus_isolation.py` — subscriber exception isolation (new)
- `tests/unit/test_search_coordinator.py` — `SearchCoordinator` unit tests (new)
- `tests/unit/ai/test_supports_events.py` — `supports_events` property (new)
- `tests/unit/test_plugin_hooks.py` — before/after file-op hooks (new)
- `tests/unit/test_plugin_types.py` — `_DARK_FALLBACK` shape (new)
- `tests/unit/test_progress_callback.py` — progress forwarding (new)
- `tests/unit/test_chat_log_styles.py` — bubble colours (new)
- `tests/unit/mcp/test_entry_default_roots.py` — MCP default home restriction (new)
- `tests/unit/ai/test_content_helpers.py` — `FileContent` / `ImageContent` (new)
- `tests/integration/test_dnd_utils.py` — `make_path_mime` (new)
- `tests/integration/test_panel_buttons.py` — panel chrome buttons (new)
- `tests/integration/test_main_window_close.py` — window close lifecycle (new)
- `tests/integration/test_main_window_ui.py` — main window UI invariants (new)

**48-killer-features test additions (~700 new tests; total: ~1015 unit + ~452 integration)**
- `tests/unit/`: test_conflict_resolver, test_highlight_rules, test_tag_store, test_finder_tags,
  test_sftp_vfs, test_view_state, test_workspace_store, test_command_store, test_search_template_store,
  test_sync_presenter, test_sync_nav_visibility, test_temp_presenter, test_nl_ops_presenter,
  test_ai_rename_presenter, test_duplicate_presenter, test_fuzzy_presenter, test_fuzzy_filter,
  test_context_actions, test_archive_cmd, test_checksum_cmd, test_dir_size, test_shell_vars,
  test_watcher, test_transfer_queue, test_ai_shell_detect, test_directory_model_git,
  test_custom_columns, test_filter_highlight, test_settings_git_preview, test_progress_copy_conflict,
  test_pane_virtual, test_flat_view, test_select_by_pattern, test_batch_rename, test_inline_rename,
  test_command_run, test_command_store, test_open_terminal_here, test_search_virtual, test_terminal_panel
- `tests/unit/preview/`: test_archive_provider, test_hex_provider, test_metadata_provider,
  test_pdf_provider, test_quicklook_provider, test_video_provider
- `tests/unit/git/`: test_status_cache, test_git_diff_provider, test_git_stage_cmd
- `tests/integration/`: test_conflict_dialog, test_transfer_queue_panel, test_batch_rename_dialog,
  test_sync_dialog, test_sync_nav_ui, test_temp_panel, test_highlight_rules_dialog, test_tag_dialog,
  test_ai_rename_dialog, test_ai_context_dialog, test_nl_ops_dialog, test_workspace_dialog,
  test_sidebar_panel, test_duplicate_dialog, test_terminal_panel, test_checksum_dialog, test_fuzzy_finder,
  test_fuzzy_quick_filter, test_fullscreen_viewer, test_select_pattern_dialog, test_column_visibility,
  test_filter_highlight, test_archive_context, test_f2_rename, test_open_terminal_shortcut,
  test_search_dialog_templates, test_watch_mode, test_breadcrumb_siblings

- Existing suites extended: `test_stream_parse`, `test_ai_providers`, `test_bookmark_store`,
  `test_bookmark_store_tree`, `test_glass_theme`, `test_pane_refresh_cursor`, `test_config`,
  `test_tabs_title_update`, `test_preview_presenter`, `test_settings_dialog`

## [v0.17.3] — 2026-07-16

### Fixed
- **Splitter 50/50 startup** — `MainWindow.showEvent` calls `setSizes` with equal halves so both
  panes start at 50/50 regardless of saved geometry
- **Glass QMenu opacity** — removed `_MenuOpaqueFilter` and `install_menu_guard`; QMenu opacity is
  now handled by proper parent (`QMenu(self.window())`) so menus inherit the correct palette
  naturally without a separate filter; `_GlassClearFilter` and `mark_glass` recursive traversal
  both skip `QMenu` instances

### Added
- **`pane_sizes()`** on `PanelCoordinator` — returns current pixel sizes of the two panes as
  `tuple[int, int]`; used by splitter tests
- **`QSize`** exported from `qt.py` compat shim

### Tests
- `tests/unit/test_splitter_sizes.py` — 5 tests (`_pad_sizes` helper)
- `tests/integration/test_splitter_layout.py` — 6 tests (50/50 startup, ratio presets, breadcrumb
  minimum size)
- `tests/unit/test_glass_style.py` — +2 tests (`recursive_skips_qmenu`,
  `recursive_skips_splitter_handle`)

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
