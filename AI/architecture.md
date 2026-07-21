# Biome FM Architecture

## Overview

```
src/biome_fm/
├── __main__.py         # CLI entry point: dispatches known subcommands (configure/doctor/version/uninstall)
│                       #   via cli/cli.dispatch() before importing Qt; falls through to QApplication bootstrap
├── app.py              # create_app() factory — full DI wiring (VFSRouter, Config,
│                       #   Session, Plugins, AI, CommandPalette, PaneSideViews);
│                       #   _AppContext dataclass keeps all long-lived objects alive (replaces window._refs tuple);
│                       #   _AI_MODEL_FIELDS dict maps 6 provider keys → config field names;
│                       #   Sub-initializers extracted: _build_plugins(cfg), _build_panes(vfs),
│                       #     _build_preview(cfg) — construction only, no signal wiring;
│                       #   SearchCoordinator wired to Ctrl+Shift+F, owns dialog/thread/queue/drain;
│                       #   nav/DnD/context-menu signal wiring; focus tracking → active pane bus;
│                       #   _op_items(): marked items → cursor item fallback (TC behavior);
│                       #   refresh_timer: 5-second QTimer calls manager._refresh_both(),
│                       #   skipped while _progress_dialogs active;
│                       #   _copy_path: exports marked paths to clipboard (newline-joined); falls back to cursor item;
│                       #   _quick_look/_reveal_in_finder closures;
│                       #   Ctrl+Z/Ctrl+Shift+Z/F3/Ctrl+I/Ctrl+R/Ctrl+W/Ctrl+Shift+C/Ctrl+Shift+L shortcuts;
│                       #   _wire_pane() / _wire_ctx() / _new_tab(side=None) helpers;
│                       #   ClipboardService wired to Ctrl+X/C/V; cut_paths pushed to DirectoryModel;
│                       #   TrashCmd wired to Delete key; FrecencyStore records on pane navigate;
│                       #   DirStateStore save/restore per-dir sort+filter state;
│                       #   GitStatusWorker wired to pane navigate → status bar git badges;
│                       #   PreviewPanel mode buttons: Text/Hex/Log/Blame/AI (new in v0.20);
│                       #   ScriptPreviewProviders loaded from ~/.config/biome-fm/preview-scripts/;
│                       #   TabsPresenter deferred-tab loading: tabs restore paths lazily on activate;
│                       #   global UI zoom: Ctrl+= / Ctrl+- / Ctrl+0 adjusts app.font() point size
│                       #   and calls app.setFont() — all panes reflow immediately
├── qt.py               # Centralised PySide6 imports (Anki pattern); includes QMimeData, QDrag
├── config.py           # @dataclass Config + TOML loader (save_config / load_config);
│                       #   new fields: follow_system_theme (bool), editor_cmd (str),
│                       #   layout_profiles (dict[str,dict] — save/load named splitter layouts);
│                       #   toolbar_actions (list[str]), toolbar_visible (bool);
│                       #   ui_font_size (int, 0=system), reduce_motion (bool), high_contrast (bool);
│                       #   global_hotkey (str), serial_ops (bool)
├── session.py          # SessionState / PaneSideState / TabState / PanelSession → JSON persistence;
│                       #   PanelSession.overlay_side persists which pane the panel occupies;
│                       #   PaneSideState.view_mode persists gallery/list view mode per pane (F456)
├── panel_manager.py    # Pure-Python state machine (no Qt); states: HIDDEN / OVERLAY / FLOATING;
│                       #   Effect dataclass (kind, target_side); kind values:
│                       #   show_overlay, show_floating, hide, focus_floating, set_opposite_visible;
│                       #   PanelManager.toggle(name, active_side) → list[Effect]
├── event_bus.py        # Decoupled pub/sub (EventBus singleton);
│                       #   events: FilesChanged, ActivePaneChanged, OperationStarted,
│                       #   OperationFinished, PaneNavigated, SyncBrowsingToggled,
│                       #   BookmarkChanged, ThemeChanged(name, tokens),
│                       #   ShowHiddenToggled(enabled: bool),
│                       #   AsyncOpSubmitted(task_id, description, cancel);
│                       #   RemoteConnected(scheme, host) — remote VFS connected;
│                       #   RemoteDisconnected(scheme, host) — remote VFS closed;
│                       #   RemoteSyncing(scheme, host, active) — remote I/O in progress;
│                       #   IPCCommandReceived(payload: dict) — external IPC command (F409)
│
├── models/
│   ├── file_item.py        # FileItem frozen dataclass (slots=True); size_str property;
│   │                       #   symlink_target: str | None field; is_broken_link: bool field
│   ├── vfs.py              # VFSProtocol + LocalVFS;
│   │                       #   LocalVFS.stat() populates symlink_target + is_broken_link
│   ├── vfs_router.py       # VFSRouter: path ancestry walk → archive root detection;
│   │                       #   dispatches local/archive; caches ArchiveVFS per archive file
│   ├── archive_vfs.py      # ZIP/TAR VFS (stdlib zipfile + tarfile, no fsspec);
│   │                       #   _child_of(raw, prefix, *, skip_dot) free fn — shared by ZIP
│   │                       #   and TAR listing; returns (child_name, is_nested) | None
│   ├── directory_model.py  # QAbstractTableModel (4 built-in cols: Name/Size/Modified/Ext);
│   │                       #   flags() adds ItemIsDragEnabled (DnD root-cause fix);
│   │                       #   ForegroundRole: file-type coloring via _EXT_COLORS dict
│   │                       #   (archives=orange, images=pink, code=green, docs=blue, media=yellow);
│   │                       #   hidden files dimmed (#565F89); ToolTipRole = path + modified + size;
│   │                       #   DirSortFilterProxy: '..' pinned first, dirs before files,
│   │                       #   set_filter(text) for Quick Filter,
│   │                       #   set_show_hidden(bool) hides dotfiles when False;
│   │                       #   canFetchMore/fetchMore for virtual scroll (large dirs);
│   │                       #   set_cut_paths(paths) dims cut items (strikethrough alpha);
│   │                       #   _dir_sizes dict: populated by bg thread, shown in Size col for dirs;
│   │                       #   natural sort: natsort_key() sorts file10 after file9;
│   │                       #   symlink display: Name column shows "name → target" for symlinks;
│   │                       #   broken symlinks shown with red foreground;
│   │                       #   set_plugin_manager(pm): wires extra_columns hook → appends ColumnDef
│   │                       #   columns; column_value hook supplies per-cell data for plugin columns
│   ├── bookmark_node.py    # BookmarkNode dataclass (kind: Literal["dir","submenu","separator"],
│   │                       #   path: Path | None, name: str, children: list[BookmarkNode]);
│   │                       #   display_label(node) free fn
│   ├── bookmark_store.py   # Tree-based TOML store; _nodes: list[BookmarkNode];
│   │                       #   primary API: tree() / set_tree(nodes);
│   │                       #   compat API: add/remove/__contains__/all/get_name/set_name/display_label;
│   │                       #   TOML: [[bookmarks.items]] with kind/path/name/depth (flat+depth for nesting);
│   │                       #   migration: old paths/names arrays → tree nodes on first load
│   ├── icon_provider.py    # icon_for_extension(ext) — @lru_cache(256), QFileIconProvider;
│   │                       #   icon_for_dir() — SP_DirIcon; fallback to SP_FileIcon
│   ├── markdown_renderer.py # Backward-compat shim — re-exports render/FENCE_RE/PRE_RE from
│   │                        #   preview/markdown_renderer.py; real implementation lives there
│   ├── sftp_vfs.py         # SFTPVfs (paramiko, optional dep); parse_sftp_uri() → SFTPSession;
│   │                        #   SFTPSession frozen dataclass (host, port, user, remote_path, proxy_command);
│   │                        #   connect/list_dir/read_file/stat/disconnect; SFTPVfs.available() guard;
│   │                        #   utime(path, mtime) preserves remote file timestamp after upload;
│   │                        #   open_read(path, offset=0) → streaming read from byte offset (resume);
│   │                        #   exec_find(remote_dir, name_pattern) → list[str] via SSH exec + shlex.quote;
│   │                        #   connect() accepts proxy_command → paramiko.ProxyCommand (jump host / tunnel);
│   │                        #   make_jump_proxy_command(jump_host, jump_port, jump_user, target_host, target_port) → str
│   ├── view_state.py       # ViewState dataclass (sort_col, sort_asc, filter) — per-dir UI state
│   ├── conflict_resolver.py # ConflictAction enum (OVERWRITE/OVERWRITE_ALL/SKIP/SKIP_ALL/RENAME/CANCEL);
│   │                        #   auto_rename(dst) → unique path (foo.txt → foo_1.txt);
│   │                        #   used by copy/move ops for non-destructive handling
│   ├── app_chooser.py      # discover_apps() → list[{name, command}]; platform-specific:
│   │                        #   macOS: mdfind .app bundles; XDG: .desktop files; Win32: stub
│   ├── associations.py     # FileAssociations — JSON-backed {suffix: app_command} map;
│   │                        #   get/set/save; used by OpenWithDialog for per-ext defaults
│   ├── clipboard_service.py # ClipboardService — Qt-free in-memory cut/copy/paste for file paths;
│   │                        #   ClipboardEntry dataclass (paths, is_cut); deque(maxlen=20) history ring;
│   │                        #   cut(paths)/copy(paths)/paste(dest) → (paths, is_cut);
│   │                        #   history() → list[ClipboardEntry]; restore_history(entry) (F446);
│   │                        #   has_cut: set[Path] for dimming cut items in the file list
│   ├── config_bundle.py    # export_config(config, dest) + import_config(src) → dict;
│   │                        #   TOML import/export; import validates against Config field names
│   ├── dir_state_store.py  # DirStateStore — JSON-backed per-dir ViewState with LRU eviction (max 500);
│   │                        #   save(dir_path, state) / load(dir_path) → ViewState | None;
│   │                        #   atexit flush via atomic tmp-replace
│   ├── file_indexer.py     # FileIndexer (QObject) — SQLite FTS5 background indexer;
│   │                        #   index_dir(path) spawns daemon thread; indexing_done Signal;
│   │                        #   search(query) → list[Path] via FTS5 MATCH
│   ├── frecency_store.py   # FrecencyStore — JSON-backed frecency tracker for dirs (max 200);
│   │                        #   record(path), score(entry) = visits/(age_secs+3600);
│   │                        #   top(n) → list[FrecencyEntry] sorted by score; atexit flush
│   ├── gitignore_filter.py # GitignoreFilter(repo_root) — is_ignored(path) via `git check-ignore -q`
│   ├── project_detector.py # detect_project(path) → ProjectInfo | None;
│   │                        #   walks up looking for pyproject.toml/package.json/Cargo.toml/etc;
│   │                        #   ProjectInfo(type, root, name); MARKERS dict covers 7 ecosystems
│   ├── script_runner.py    # ScriptRunner(script_dir) — discovers *.py/*.sh scripts;
│   │                        #   run(script, selected, cwd) → CompletedProcess;
│   │                        #   injects BIOME_SELECTED + BIOME_CWD + BIOME_IPC_PORT env vars; path-escape guard
│   ├── shortcut_store.py   # ShortcutStore — JSON-backed {action: key_sequence} map; get/set/save/load
│   ├── tab_group_store.py  # TabGroupStore — JSON-backed named tab groups;
│   │                        #   save_group/load_group/list_groups/delete_group
│   ├── template_store.py   # TemplateStore + FileTemplate(name, ext, content);
│   │                        #   BUILTIN templates: Python Script, Markdown, Text File;
│   │                        #   used by NewFileCmd for pre-populated content
│   ├── user_actions.py     # UserActionsStore + UserAction(label, command, extensions);
│   │                        #   add/update/remove/all/actions_for(suffix)/save/load;
│   │                        #   JSON persistence; filtered by extension list or all if empty
│   ├── volume_watcher.py   # VolumeWatcher (QObject) — polls OS for hot-plug volumes (3s timer);
│   │                       #   volume_added/volume_removed Signals(Path);
│   │                       #   macOS: /Volumes; Linux: /proc/mounts; Windows: drive letters
│   ├── archive_7z.py       # SevenZipVFS: read-only VFS for .7z via py7zr (optional dep);
│   │                       #   RarVFS: read-only VFS for .rar via rarfile (optional dep);
│   │                       #   both reuse _child_of() from archive_vfs.py; listdir + read_bytes
│   ├── fsspec_vfs.py       # FsspecVFS: VFS adapter for any fsspec protocol (S3, FTP, WebDAV);
│   │                       #   __init__(url, **storage_options) — protocol extracted from url;
│   │                       #   listdir/stat/exists/read_bytes/copy/put/get/move/delete/mkdir;
│   │                       #   guards against missing fsspec with ImportError on construction;
│   │                       #   utime(path, mtime) — delegates to fs.touch() or silent no-op if unsupported;
│   │                       #   open_read(path, offset=0) → seekable read from byte offset (cross-VFS resume)
│   ├── opener_rules.py     # Declarative file-opener rules loaded from TOML;
│   │                       #   OpenerRule(match, cmd) — glob pattern + command template with {};
│   │                       #   load_rules(path) → list[OpenerRule]; find_opener(rules, filename)
│   │                       #   → first matching cmd | None (case-insensitive fnmatch)
│   ├── ssh_profiles.py     # SSHProfile(name, host, port, user, key_path, jump_host, jump_user) — no passwords stored;
│   │                       #   jump_host/jump_user fields enable SSH tunnel via make_jump_proxy_command();
│   │                       #   SSHProfileStore: TOML-backed add/get/delete/list_all/save/load;
│   │                       #   import_ssh_config(path) parses OpenSSH config Host entries
│   │                       #   (skips wildcard hosts); TOML: [profiles.<name>] sections
│   ├── sync_profiles.py    # SyncProfile(name, src, dst, exclude, mirror) dataclass;
│   │                        #   SyncProfileStore: TOML-backed add/get/delete/list_all/save/load;
│   │                        #   TOML: [profiles.<name>] sections; _esc() escapes TOML strings
│   ├── select_criteria.py  # SelectCriteria dataclass (name_glob, extensions, min/max_size,
│   │                        #   min/max_age_days); matches(item) → bool; pure-Python predicate
│   │                        #   for multi-criteria file selection (F221)
│   ├── user_menu.py        # UserMenuItem(name, command, shortcut) dataclass;
│   │                        #   load_user_menu(cwd, global_config) → list[UserMenuItem];
│   │                        #   walks up from cwd for .biome-menu.toml; falls back to global config
│   ├── credential_store.py # get_credential/set_credential/delete_credential — keyring when
│   │                        #   available, in-process dict fallback; logs warning once if keyring absent
│   ├── finder_tags.py      # macOS Finder tags + quarantine xattr helpers;
│   │                        #   get_tags(path)/set_tags(path, tags) via com.apple.metadata:_kMDItemUserTags;
│   │                        #   remove_quarantine_flag(path) removes com.apple.quarantine xattr;
│   │                        #   get_finder_comment(path)/set_finder_comment(path, comment) via
│   │                        #   com.apple.metadata:kMDItemFinderComment xattr; non-macOS fallback
│   │                        #   uses hidden sidecar .{name}.biome-meta.json (JSON {comment: str});
│   │                        #   _getxattr/_setxattr wrappers; macOS-only (no-ops on other platforms)
│   ├── cloud_profile_store.py # CloudProfile(name, scheme, host, port, user, bucket, extra);
│   │                           #   CloudProfileStore: TOML-backed CRUD;
│   │                           #   schemes: s3/sftp/ssh/ftp/ftps/webdav/rclone;
│   │                           #   path: ~/.config/biome-fm/cloud_profiles.toml
│   ├── remote_cache.py     # RemoteListCache — thread-safe (RLock) TTL=30s cache for remote
│   │                        #   directory listings; get/set/invalidate; key = str(path)
│   ├── rclone_vfs.py       # RcloneVFS — VFS backed by `rclone lsjson` subprocess;
│   │                        #   listdir/stat/copy/move/delete/mkdir via JSON API;
│   │                        #   _parse_modtime handles nanosecond suffixes in rclone timestamps;
│   │                        #   ponytail: subprocess-per-call — replace with rclone serve for throughput
│   ├── preview_file_cache.py # PreviewFileCache — SHA1-keyed local temp files for remote preview;
│   │                          #   50 MB max (configurable); LRU eviction; thread-safe (Lock);
│   │                          #   get(path, mtime) → local Path | None; set/evict
│   ├── cloud_connection_store.py # CloudConnectionStore — JSON-backed list of cloud URLs
│   │                              #   (s3://, ftp://, etc.); add/remove/list/load/save
│   ├── deps_scanner.py     # scan_cleanup_dirs(root, cancel, max_depth=6, patterns=None) → list[Path];
│   │                        #   walks root collecting dirs matching _DEFAULT_PATTERNS frozenset
│   │                        #   (node_modules, __pycache__, .venv, venv, target, dist, build, etc.);
│   │                        #   patterns kwarg overrides defaults (used by SpaceReclaimerPresenter);
│   │                        #   cancel=threading.Event for cooperative stop; Qt-free
│   ├── url_signer.py       # sign_url(path, vfs, expiration=3600) → str | None;
│   │                        #   presigned/shareable URL for remote VFS files; Qt-free;
│   │                        #   FsspecVFS: delegates to fs.sign(); RcloneVFS: subprocess rclone link;
│   │                        #   returns None when VFS doesn't support signing
│   ├── fish_vfs.py         # FISHVfs — SSH exec_command VFS for devices without SFTP subsystem;
│   │                        #   listdir() via `ls -la --time-style=long-iso`, read_file() via `cat`;
│   │                        #   _parse_ls_line() parses long-format ls output; shlex-quoted commands;
│   │                        #   paramiko dep; proxy_command param for jump hosts; _HAS_PARAMIKO guard
│   ├── script_vfs.py       # extfs-style Script VFS — archive browsing via external shell scripts;
│   │                        #   ScriptVFSSpec(extensions, list_cmd, read_cmd, timeout) frozen dataclass;
│   │                        #   {archive}/{dir}/{path} template placeholders; ScriptVFS.listdir/read;
│   │                        #   load_script_vfs_specs(dir) loads *.toml from spec directory;
│   │                        #   covers RPM/DEB/ISO and user-defined archive formats; read-only
│   ├── iso_vfs.py          # IsoVFS — read-only ISO 9660 browser via pycdlib (optional dep);
│   │                        #   listdir/read_bytes; _to_iso_path() maps Path → ISO path string;
│   │                        #   strips Joliet ;1 version suffix from filenames; ImportError guard
│   ├── dmg_vfs.py          # DmgVFS — macOS DMG browser via hdiutil subprocess;
│   │                        #   mount() attaches image (readonly+nobrowse), parses plist output;
│   │                        #   unmount() calls hdiutil detach; context manager __enter__/__exit__;
│   │                        #   RuntimeError if not darwin; listdir/read_bytes delegate to LocalVFS on mount point
│   ├── docker_vfs.py       # DockerVFS — Docker container filesystem browser;
│   │                        #   listdir() via `docker exec ls -la`; read_bytes() via `docker cp` + tarfile;
│   │                        #   _parse_docker_ls() parses long-format output; _LS_RE regex;
│   │                        #   docker_available() guard (shutil.which); list_containers() helper
│   ├── filter_predicate.py  # FilterSpec dataclass (name, ext, size_op, size_bytes, mod_period);
│   │                        #   parse_filter(text) → FilterSpec: tokenises "size:>10m mod:today ext:py foo";
│   │                        #   filter_accepts(spec, name, size, modified, is_dir) → bool;
│   │                        #   pure Python — no Qt, no FileItem dep; used by advanced filter bar (F415)
│   ├── metadata_reader.py   # read_metadata(path) → dict[str, str]: EXIF (piexif, optional) for
│   │                        #   .jpg/.tiff; audio tags (mutagen, optional) for .mp3/.flac/.ogg/.m4a;
│   │                        #   empty dict on missing deps or read errors; used by [META:key] token (F428)
│   ├── watch_rules.py       # WatchRule(watch_dir, pattern, command) dataclass;
│   │                        #   WatchRuleStore: TOML-backed add/remove/all/load/save;
│   │                        #   path: ~/.config/biome-fm/watch_rules.toml;
│   │                        #   WatchRuleEngine: snapshot-diff engine — check_dir(watch_dir) detects
│   │                        #   new files, matches fnmatch pattern, runs shell command with {file};
│   │                        #   on_fired callback for UI notification; F422
│   ├── session_store.py    # SessionStore — JSON-backed named sessions;
│   │                        #   save(name, state) / load(name) → SessionState | None;
│   │                        #   list() / delete(name); wraps session.py SessionState dataclasses;
│   │                        #   persists PaneSideState.view_mode field (F456)
│   └── macro_store.py      # MacroStore — JSON-backed keyboard macro storage;
│                            #   save(name, keystrokes) / load(name) → list[str] | None;
│                            #   list() / delete(name); path: ~/.config/biome-fm/macros.json (F457)
│
├── presenters/
│   ├── pane_presenter.py     # Drives one pane (cd, select, sort, current_item);
│   │                         #   PaneViewProtocol: set_items/set_path/show_error/set_status/
│   │                         #   set_marked/current_cursor_item/advance_cursor/retreat_cursor/
│   │                         #   set_filter_visible/select_item;
│   │                         #   _navigate_no_history(path, *, initial_cursor=None): optional
│   │                         #   cursor name placed after reload if item still exists;
│   │                         #   refresh() captures current_cursor_item() before reload so
│   │                         #   cursor stays on same file after auto-refresh or F5;
│   │                         #   back/forward stacks; archive in-pane via _is_archive()
│   │                         #   (_ARCHIVE_SUFFIXES: .zip/.tar/.tar.gz/.tar.bz2/.tgz; .7z excluded);
│   │                         #   go_up() calls select_item(prev_name) so cursor lands on the
│   │                         #   folder the user came from (classic FM UX);
│   │                         #   _update_status: marks + free-space (cached disk_usage); _fmt_size;
│   │                         #   selection ops: toggle_mark/toggle_mark_up/select_all/
│   │                         #   deselect_all/invert_selection/select_by_pattern/deselect_by_pattern;
│   │                         #   persistent marks: _marks set[Path] survives cd within the same pane;
│   │                         #   marks restored when navigating back to a dir (path-keyed set)
│   ├── tabs_presenter.py     # Owns N PanePresenters per side; duck-types as PanePresenter
│   │                         #   for ManagerPresenter; TabsViewProtocol requires set_tab_tooltip;
│   │                         #   tabs display abbreviated path (~/... or …/name if >30 chars);
│   │                         #   tooltip = full str(path); opener param passed to each PanePresenter;
│   │                         #   deferred tab loading: session paths restored lazily on first tab activate
│   ├── manager_presenter.py  # Inter-pane ops (copy, move, delete, mkdir, rename);
│   │                         #   drop_files(paths, target_pane_id, move, target_folder) — DnD;
│   │                         #   async path: ProgressCopyCmd/ProgressMoveCmd submitted to OpQueue,
│   │                         #   publishes AsyncOpSubmitted(task_id, desc, cancel);
│   │                         #   accepts plugins: PluginManager | None — calls before_file_operation
│   │                         #   hook (veto guard) and on_file_operation hook (post-op notification)
│   │                         #   for all sync + async file ops;
│   │                         #   toggle_mirror() / navigate_active() for Sync Browsing;
│   │                         #   toggle_hidden() — flips Config.show_hidden, publishes ShowHiddenToggled;
│   │                         #   undo/redo via CommandHistory → refresh_both();
│   │                         #   swap_panes() exchanges left/right pane paths + histories;
│   │                         #   move_tab_to_other_pane(tab_idx) moves active tab to opposite side
│   ├── ai_presenter.py       # AI chat bridge (AIProvider ↔ AIChatViewProtocol)
│   ├── compare_presenter.py  # Directory diff (left vs right pane);
│   │                         #   content_diff(left_item, right_item) → unified diff string;
│   │                         #   content_compare(left_item, right_item) → bool (byte-exact equality)
│   ├── rename_presenter.py   # Multi-rename (pattern, counter, ext substitution)
│   ├── search_coordinator.py # SearchCoordinator (no Qt): concurrent search state machine;
│   │                         #   owns dialog, thread, queue.SimpleQueue, drain; cancel any
│   │                         #   in-progress on new request_search(); drain() called by 50ms QTimer;
│   │                         #   wired in app.py, coordinates SearchPresenter + SearchResultsPanel +
│   │                         #   PanelCoordinator.toggle("search", ...)
│   ├── search_presenter.py   # File search (name glob + content grep);
│   │                         #   SearchScope.SYSTEM_INDEX added — delegates to system_index_search();
│   │                         #   system_index_search(query, root) → list[Path]: macOS uses mdfind -name,
│   │                         #   Linux uses locate -i; 5s timeout; root filter applied for locate results;
│   │                         #   remote_search(vfs, remote_dir, pattern) → list[str]: delegates to
│   │                         #   vfs.exec_find() when available (duck-typed); SFTP server-side find
│   ├── settings_presenter.py # SettingsPresenter (no Qt) + SettingsViewProtocol;
│   │                         #   load/save Config fields via protocol methods;
│   │                         #   tabs: General, Appearance, AI, Plugins
│   ├── editor_presenter.py   # EditorPresenter(view, path) — logic for built-in text editor;
│   │                         #   save() writes view text to path; is_modified() compares to saved_text;
│   │                         #   _EditorView Protocol (toPlainText/setPlainText)
│   ├── info_presenter.py     # InfoPresenter(view) — updates InfoPanel on cursor change;
│   │                         #   on_cursor_changed(item | None) → view.update_fields(dict);
│   │                         #   fields: name, size_str, mtime, permissions, mime type
│   ├── fuzzy_presenter.py    # FuzzyPresenter — Qt-free fuzzy file finder;
│   │                         #   scan(root, cancel, on_done) walks MAX_DEPTH=5, MAX_FILES=10k;
│   │                         #   filter(query, paths) → top 100 by difflib.SequenceMatcher score
│   ├── ai_diff_summary.py    # diff_summary_prompt(diff) → str; async summarize_diff(diff, ai_call)
│   │                         #   → summary string; truncates diff at 4000 chars before sending
│   ├── ai_group_rename.py    # async group_rename(names, ai_call) → list[str]; builds prompt asking
│   │                         #   AI to rename list coherently; parse_group_response validates count
│   ├── column_state.py       # ColumnState — tracks hidden columns (Name always visible);
│   │                         #   is_visible/set_visible/toggle/visible_columns; 4 columns: Name/Size/Modified/Kind
│   ├── copy_filter.py        # filter_by_mask(paths, mask) → list[Path];
│   │                         #   comma-separated glob patterns (e.g. "*.py,*.js"); case-insensitive fnmatch
│   ├── cross_marks.py        # CrossDirMarks — aggregated marks across multiple directories (no Qt);
│   │                         #   add/remove per directory; all_paths() flattens; count(); clear()
│   ├── drive_list.py         # VolumeInfo(root, name, free_bytes, total_bytes) dataclass;
│   │                         #   list_volumes() → list[VolumeInfo] via QStorageInfo.mountedVolumes()
│   ├── hotlist.py            # Hotlist(store) — thin wrapper over FrecencyStore.top();
│   │                         #   items(limit=10) → deduplicated list[Path] ordered by frecency score
│   ├── leader_handler.py     # LeaderHandler — vim-style leader key sequence dispatcher (no Qt);
│   │                         #   register(sequence, action); feed(key) → 'pending'|'triggered'|'reset';
│   │                         #   available() → [(remaining_keys, sequence)] for current prefix
│   ├── miller_state.py       # MillerState — columns navigation state (max MAX_COLUMNS=4);
│   │                         #   select_dir(path) appends column, evicts oldest when full;
│   │                         #   go_back() → bool; active_column property; columns property
│   ├── path_yank.py          # yank_component(path, key) → str | None;
│   │                         #   keys: n=name, p=full path, d=parent dir, e=extension
│   ├── predictive_dest.py    # suggest_destination(file_path, frecency, current_dir) → Path | None;
│   │                         #   finds frecency-ranked dir containing files with same extension
│   ├── project_actions.py    # ProjectAction(label, command) dataclass;
│   │                         #   detect_actions(directory) → list[ProjectAction]; checks for .git,
│   │                         #   pyproject.toml, package.json, go.mod; returns relevant commands
│   ├── quick_view_state.py   # QuickViewState — saves/restores splitter sizes for quick-view mode;
│   │                         #   toggle(current_sizes) → new_sizes; active property;
│   │                         #   expand: sets right pane to 0; restore: returns saved sizes
│   ├── rename_template.py    # TC-style multi-rename token expander;
│   │                         #   expand_template(template, path, index, counter_start, metadata=None) → str;
│   │                         #   tokens: [N]=stem, [E]=ext, [C]/[C:n]=counter (zero-padded 3), [YMD]=mtime;
│   │                         #   [META:key] substitutes EXIF/audio metadata from metadata dict (F428);
│   │                         #   [TOKEN:upper/lower/title] case modifiers supported
│   ├── semantic_search.py    # Keyword-based semantic search (no Qt, no ML);
│   │                         #   extract_keywords(query) strips stopwords; score_path(path, kws);
│   │                         #   search_by_keywords(paths, query) → list[(path, score)] sorted desc
│   ├── sync_conflict.py      # SyncConflict(path, left_mtime, right_mtime) dataclass;
│   │                         #   SyncSnapshot: JSON-backed per-pair {filename: {left_mtime, right_mtime}};
│   │                         #   find_conflicts(entries, snapshot) → entries where both sides changed;
│   │                         #   update_snapshot(entries, snapshot) records current mtimes
│   ├── sync_executor.py      # SyncExecutor — VFS-agnostic sync op runner;
│   │                         #   execute(ops) → int (done count); cancel threading.Event checked per op;
│   │                         #   progress(done, total, name) callback;
│   │                         #   delete_orphan ops now execute in mirror mode (F402 bug fix)
│   ├── sync_presenter.py     # SyncOp(action, src, dst, size) dataclass;
│   │                         #   Direction = "left_to_right" | "right_to_left" | "newer_wins";
│   │                         #   preview_sync(entries, direction, left_root, right_root, exclude, mirror)
│   │                         #   → list[SyncOp] (no filesystem access); build_sync_commands() → SyncPair list
│   ├── duplicate_presenter.py # find_duplicates(root, cancel) → list[DupGroup];
│   │                           #   3-stage progressive hashing: size grouping → 4 KB partial hash
│   │                           #   → full SHA-256 (skips ~90% of full reads);
│   │                           #   DupGroup(hash, paths, size); cancel=[False] for cooperative stop
│   ├── file_collector.py   # FileCollector — deduplicated multi-dir virtual panel builder;
│   │                        #   add(items)/remove(paths)/items()/count()/clear();
│   │                        #   keyed by Path; show via navigate_virtual
│   ├── treemap_presenter.py # TreemapPresenter (Qt-free) — background os.walk size scanner;
│   │                         #   squarify(nodes, x, y, w, h) → list[(node, rect)] layout;
│   │                         #   TreemapNode(path, size, color); _PALETTE 8-color list;
│   │                         #   TreemapViewProtocol.set_nodes(nodes); threading + queue drain
│   ├── omnibar_presenter.py  # OmnibarPresenter(registry, root) — Qt-free prefix dispatcher;
│   │                         #   mode_for(text) → OmniMode (NAVIGATE / COMMAND / SEARCH);
│   │                         #   "/" "~" "." prefix → path completions; ">" prefix → command registry search;
│   │                         #   bare text → semantic keyword search; query_changed(text) → list[OmniItem];
│   │                         #   OmniItem(label, subtitle, data); F411
│   ├── space_reclaimer_presenter.py # SpaceReclaimerPresenter(root, patterns, on_results) — Qt-free;
│   │                         #   start() spawns daemon thread calling scan_cleanup_dirs(root, patterns);
│   │                         #   computes size via rglob per dir; calls on_results(list[ReclaimEntry]);
│   │                         #   cancel() sets threading.Event; ReclaimEntry(path, size); F431
│   ├── uri_parser.py         # ParsedURI(scheme, host, port, path, username) dataclass;
│   │                          #   detect_scheme(text) → scheme | None; known: sftp/ssh/s3/ftp/ftps/webdav;
│   │                          #   parse_uri(text) → ParsedURI via urllib.parse.urlparse
│   └── macro_recorder.py     # MacroRecorder — records command-id sequences;
│                              #   start() / record(command_id) / stop() → list[str];
│                              #   MacroPlayer(registry).play(command_ids) runs callbacks;
│                              #   Qt-free; wired in app.py with MacroStore for persistence (F457)
│
├── views/
│   ├── main_window.py    # QMainWindow: splitter, closeEvent, splitter_sizes persistence,
│   │                     #   _build_menubar; QToolBar removed — Refresh/Preview/AI actions
│   │                     #   moved to menubar (File, View); macOS zero-height drag toolbar
│   │                     #   kept via setUnifiedTitleAndToolBarOnMac(True);
│   │                     #   command line visible by default; _on_cmd executes shell command
│   │                     #   with cwd=active pane path, emits command_submitted signal;
│   │                     #   _HistoryLineEdit (30-item dedup history, Up/Down nav) +
│   │                     #   case-insensitive QCompleter (dropdown history);
│   │                     #   signals: back/forward/up/home + undo/redo/refresh/new_tab _requested,
│   │                     #   close_tab_requested (File → Close Tab, Ctrl+W),
│   │                     #   command_submitted, about_to_close; tab_shortcut (Tab key QShortcut);
│   │                     #   splitter handle(1): 5px wide, accent on hover; RMB or MiddleButton →
│   │                     #   _show_ratio_menu(global_pos) → 25/75, 50/50, 75/25 via _set_pane_ratio();
│   │                     #   eventFilter catches QEvent.Type.ContextMenu + MiddleButton on handle
│   ├── pane_side_view.py # _PathTabBar (Ctrl+click / middle-click copies full path from tooltip);
│   │                     #   tabs movable; _sync_tab_bar() — tab bar hidden when single tab,
│   │                     #   shown with close buttons when 2+ tabs; new_tab_requested = Signal();
│   │                     #   set_tab_title() sets abbreviated display + full tooltip;
│   │                     #   set_tab_tooltip(); set_active() toggles QSS dynamic property
│   ├── pane_view.py      # QWidget: nav buttons (←→↑⌂ with tooltips) + path bar + table + bars;
│   │                     #   _PaneTableView (inner QTableView subclass): full DnD impl
│   │                     #   (mimeData/startDrag/dragEnterEvent/dragMoveEvent/dropEvent);
│   │                     #   MIME type application/x-biome-fm-paths; Shift-drop = move;
│   │                     #   key routing: Enter/Return=item_activated, Space/F3=PreviewPanel toggle,
│   │                     #   Shift+Down=mark, Shift+Up=mark_up, /=FilterBar, printable→JumpBar;
│   │                     #   context menu: Copy/Move/Delete/Rename/Copy Path/Preview/Open in Finder
│   │                     #   (platform label); setUniformRowHeights() compat stub; table: no grid,
│   │                     #   alternatingRowColors, 22px rows, vertical header hidden;
│   │                     #   Name=Stretch, Size/Modified/Ext=Interactive;
│   │                     #   retreat_cursor() for Shift+Up mark; advance_cursor() for mark;
│   │                     #   select_item(name) scrolls to and selects row by filename;
│   │                     #   _DropHintDelegate: QStyledItemDelegate draws 2px highlight border
│   │                     #   around folder row when _drop_hint_row matches; _drop_hint_row
│   │                     #   set in dragMoveEvent (folder under cursor) / cleared on dragLeave;
│   │                     #   drop on folder → emits target_folder path; drop on blank → None;
│   │                     #   nav bar layout: [◄] [►] [▲] [★ BookmarkMenu] | BreadcrumbBar(stretch) | [+];
│   │                     #   new_tab_requested signal; _btn_new_tab QPushButton at right of nav bar;
│   │                     #   Home button removed from nav bar; home_requested signal retained;
│   │                     #   11 signals: item_activated, path_change_requested,
│   │                     #   mark_toggle_requested, mark_toggle_up_requested, view_requested,
│   │                     #   back/forward/up/home_requested, new_tab_requested,
│   │                     #   context_action_requested;
│   │                     #   files_dropped = Signal(list, bool, object)
│   │                     #     → (paths: list[Path], move: bool, target_folder: Path | None);
│   │                     #   spring-loaded folders: 800ms hover timer → auto-expand folder on DnD hover;
│   │                     #   clipboard signals: cut_requested/copy_requested/paste_requested(Path);
│   │                     #   Insert key → toggle_mark_requested (marks without advancing cursor);
│   │                     #   mouse back/forward buttons (Qt.MouseButton.BackButton/ForwardButton)
│   │                     #   emit back_requested/forward_requested in mousePressEvent;
│   │                     #   trackpad two-finger swipe: horizontal wheelEvent on _PaneTableView
│   │                     #   accumulates angleDelta().x() → back/forward with 300ms cooldown
│   ├── dnd_utils.py      # make_path_mime(paths, *, urls=True) → QMimeData; builds
│   │                     #   biome-fm-paths + uri-list + text/plain; urls=False omits uri-list
│   │                     #   (Alt-drag text-only); _MIME constant owned here; used by
│   │                     #   _PaneTableView.mimeData() and _SegmentButton drag
│   ├── _panel_buttons.py # add_panel_buttons(header_layout, detach, close): shared ⬒/✕
│   │                     #   chrome for overlay panels (24×24 buttons with tooltips)
│   ├── filter_bar.py     # FilterBar: QLineEdit-based quick filter; hidden by default;
│   │                     #   activate() shows + focuses; Escape → deactivate + closed signal;
│   │                     #   filter_changed(str) signal → DirSortFilterProxy.set_filter()
│   ├── jump_bar.py       # JumpBar: type-to-navigate overlay label; append_char() accumulates
│   │                     #   keystrokes, emits jump_text_changed(str); auto-clears after 600ms;
│   │                     #   PaneView._on_jump() scans proxy rows for prefix match
│   ├── ai_chat_panel.py  # Passive AI chat (message_submitted Signal)
│   ├── action_bar.py     # F1-F10 function key bar (tooltips on all buttons)
│   ├── command_palette.py # Fuzzy-search command launcher (Ctrl+P);
│   │                     #   results sorted by hit count from CommandRegistry.search()
│   ├── preview_panel.py  # PreviewPanel (QWidget): QStackedWidget with 3 widgets
│   │                     #   (busy label, image QLabel, QTextBrowser); animated slide on
│   │                     #   maximumWidth (150ms OutCubic); DEFAULT_WIDTH=350;
│   │                     #   visibility_changed(bool) signal; implements PreviewViewProtocol;
│   │                     #   set_code_alpha(alpha) controls code block opacity in MD preview;
│   │                     #   mode toolbar: Text/Hex/Log/Blame/AI buttons; Log + Blame route to
│   │                     #   GitLogPreviewProvider / GitBlamePreviewProvider on demand;
│   │                     #   AI button triggers AI summary of current file via AIPresenter;
│   │                     #   word wrap toggle: Wrap button → QTextBrowser.setLineWrapMode;
│   │                     #   text zoom: Ctrl+Wheel → QTextBrowser.zoomIn()/zoomOut();
│   │                     #   Tail button (checkable) → tail_toggled Signal(bool) → PreviewPresenter.set_tail_mode()
│   ├── panel_coordinator.py  # QObject: dispatches Effect → Qt widget ops;
│   │                         #   accepts left_side + right_side PaneSideView widgets;
│   │                         #   toggle(name, active_side="left") opens panel in the
│   │                         #   OPPOSITE pane (active left → right; active right → left);
│   │                         #   _saved_sizes keyed by widget; _hidden_widget tracks displaced pane;
│   │                         #   detach() creates floating QDialog; save_state/restore_state
│   │                         #   round-trips overlay_side to PanelSession;
│   │                         #   toggle_fullscreen_shell() (Ctrl+O): shows TerminalPanel full-window,
│   │                         #   hides both pane sides; toggles back on second press (F406)
│   ├── breadcrumb_bar.py # BreadcrumbBar: QStackedWidget (breadcrumb ↔ edit modes);
│   │                      #   segment buttons are DnD drop targets (accept files_dropped);
│   │                      #   breadcrumb mode = _CrumbRow with _SegmentButton per path segment;
│   │                      #   edit mode = inline _PathComboBox; click segment → navigate;
│   │                      #   RMB context: Copy Path / Copy Name / Show in Finder / Open Terminal Here;
│   │                      #   horizontal wheel/swipe → back/forward (threshold 120, 300ms cooldown);
│   │                      #   signals: path_entered(str), back_requested, forward_requested;
│   │                      #   path_segments(path) → list[(label, Path)] pure helper (no Qt)
│   ├── settings_dialog.py # QDialog (4 tabs: General/Appearance/AI/Plugins);
│   │                      #   passive view implementing SettingsViewProtocol;
│   │                      #   General: show_hidden QCheckBox, sync_browsing QCheckBox;
│   │                      #   Appearance: theme QComboBox, file_type_colors QCheckBox;
│   │                      #   AI: provider QComboBox, API key QLineEdits, Ollama URL/model;
│   │                      #   Plugins: read-only QListWidget of installed plugins
│   ├── progress_dialog.py # Modeless QDialog for async file ops; shows file label,
│   │                      #   bytes QProgressBar, overall label, files QProgressBar, Cancel button;
│   │                      #   update(files_done, files_total, bytes_done, bytes_total, name);
│   │                      #   Cancel button sets threading.Event; auto-closes on OpDone/OpCancelled
│   ├── _zoomable_image.py  # ZoomableImageWidget (QScrollArea) — zoom/pan/rotate for image preview;
│   │                       #   Ctrl+= zoom in (×1.25), Ctrl+- zoom out, Ctrl+0 reset; R key rotates 90°;
│   │                       #   fit-to-window mode (F key or button): scales pixmap to viewport;
│   │                       #   1:1 mode: resets to original pixel size
│   ├── archive_format_dialog.py # ArchiveFormatDialog — select archive name + format (zip/tar.gz/tar.bz2)
│   ├── diff_view_dialog.py # DiffViewDialog(diff, title) — unified diff with Pygments syntax highlight;
│   │                        #   falls back to <pre> if Pygments absent
│   ├── dir_tree_panel.py   # DirTreePanel (QWidget) — QFileSystemModel tree (dirs only);
│   │                        #   path_selected Signal(Path) on activation; set_root(path) scrolls to dir
│   ├── disk_usage_widget.py # DiskUsageWidget (QProgressBar) — compact 120px bar;
│   │                         #   update_path(path) calls shutil.disk_usage; tooltip shows free GB
│   ├── editor_dialog.py    # EditorDialog — built-in QPlainTextEdit editor (QDialog);
│   │                        #   Ctrl+S saves via EditorPresenter; saved Signal(Path); unsaved-changes guard;
│   │                        #   find/replace toolbar: Ctrl+F → show; QTextDocument.find() for next/prev;
│   │                        #   replace/replace-all via setPlainText; go-to-line: Ctrl+G → line number input
│   ├── fayt_bar.py         # FAYTBar (Find-As-You-Type) — QLineEdit with mode prefix dispatch;
│   │                        #   / → navigate_requested, : → command_requested, ? → search_requested,
│   │                        #   no prefix → filter_changed; replaces FilterBar + JumpBar combo
│   ├── git_commit_dialog.py # GitCommitDialog(repo, ai_call) — staged file list + message QPlainTextEdit;
│   │                         #   "Suggest" button → _AISuggestWorker (QRunnable in QThreadPool):
│   │                         #   calls staged_diff(repo) → diff_summary_prompt(diff) → ai_call → fills message;
│   │                         #   ai_call may be a coroutine (asyncio.new_event_loop per worker thread);
│   │                         #   Ok commits via commit_ops.commit(); requires git staged files
│   ├── git_stash_dialog.py # GitStashDialog — passive view; stash_apply/pop/drop/new/refresh Signals;
│   │                        #   parse_stash_list(raw) → list[str] free fn; list + Apply/Pop/Drop/New btns
│   ├── info_panel.py       # InfoPanel (QWidget) — QFormLayout sidebar: name/size/mtime/permissions/MIME;
│   │                        #   clear() / update_fields(dict) driven by InfoPresenter
│   ├── jump_dialog.py      # JumpDialog — frecency quick-jump dialog (Ctrl+J);
│   │                        #   live filter QLineEdit; path_selected Signal(Path); Esc/Return shortcuts
│   ├── menu_builder_dialog.py # MenuBuilderDialog — list/add/edit/remove UserActions via UserActionsStore;
│   │                           #   Tool window; form: label, command, extensions; Save on accept
│   ├── op_log_panel.py     # OpLogPanel + OpLogModel (QAbstractTableModel) — live operation log;
│   │                        #   columns: Time/Operation/Status/Details; deque(max=500); add_entry(op,status,details)
│   ├── open_with_dialog.py # OpenWithDialog — discover_apps() list + custom command QLineEdit;
│   │                        #   app_selected Signal(str) emits command string; double-click or OK to confirm
│   ├── properties_dialog.py # PropertiesDialog(item) — 3-tab QDialog: General / Permissions / Extended Attrs;
│   │                         #   General: name/size/mtime + Finder Comment QTextEdit (saved to kMDItemFinderComment
│   │                         #   xattr or .biome-meta.json sidecar on non-macOS); Ok button saves comment;
│   │                         #   Permissions: 9 QCheckBox bits (rwxrwxrwx), read-only on non-POSIX;
│   │                         #   Extended Attrs: QTableWidget (Key/Value), Add/Remove buttons,
│   │                         #   inline edit via os.setxattr; uses os.listxattr/getxattr (macOS/Linux)
│   ├── sftp_connect_dialog.py # SFTPConnectDialog — host/port/user/password form;
│   │                           #   connect_requested Signal(host, port, user, password)
│   ├── shortcut_help_dialog.py # ShortcutHelpDialog — static cheatsheet QTextBrowser (? or F1);
│   │                            #   SHORTCUTS dict: 28 bindings rendered as HTML table
│   ├── copy_move_dialog.py # CopyMoveDialog(op, sources, default_dest, history) — TC-style
│   │                        #   copy/move destination with editable QComboBox path + browse button
│   ├── select_criteria_dialog.py # SelectByAttrDialog — builds SelectCriteria from user input;
│   │                               #   fields: name glob, extensions, min/max size, age days
│   ├── quick_cd_dialog.py  # QuickCDDialog — frecency + live path-completion quick-CD (Alt+C);
│   │                        #   path_selected Signal(Path)
│   ├── permissions_editor_dialog.py # Bulk chmod dialog — 9 QCheckBox bits (rwxrwxrwx);
│   │                                 #   common mode for mixed selections; POSIX-only
│   ├── which_key_popup.py  # WhichKeyPopup — floating monospace hint overlay (ToolTip window);
│   │                        #   show_hints(hints, parent) displays key→sequence pairs
│   ├── leader_filter.py    # LeaderFilter (QObject) — QApplication event filter for leader sequences;
│   │                        #   ignores QLineEdit/QTextEdit; 300ms timeout; action_triggered Signal(str)
│   ├── cloud_profile_dialog.py # CloudProfileDialog — CRUD dialog for CloudProfileStore;
│   │                            #   list pane (left) + edit form (right); scheme QComboBox
│   ├── quick_connect_bar.py # QuickConnectBar — QComboBox + Connect button;
│   │                         #   connect_requested Signal(uri: str)
│   ├── upload_queue_panel.py # UploadQueuePanel — passive view for upload queue;
│   │                          #   add_upload/on_progress/on_complete/on_error per task_id
│   ├── editor_highlighter.py # PygmentsHighlighter (QSyntaxHighlighter) — Pygments-backed
│   │                          #   syntax highlighting for EditorDialog; theme-aware; 512 KB guard
│   ├── group_delegate.py   # GroupDelegate (QStyledItemDelegate) — accent separator + group label
│   │                        #   above first row of each group; reads GROUP_ROLE from proxy
│   ├── large_file_dialog.py # LargeFileDialog — scan_large_files() os.walk; configurable min-size;
│   │                         #   sortable QTableView; top-100 results
│   ├── treemap_panel.py    # TreemapPanel (QWidget) — QPainter squarify storage treemap;
│   │                        #   hover tooltip; path_clicked Signal(Path); wired to TreemapPresenter
│   ├── session_picker_dialog.py # SessionPickerDialog — browse, save, delete named sessions;
│   │                             #   wraps SessionStore; selected_name attr on Load
│   ├── task_runner_dialog.py # TaskRunnerDialog — Makefile/Justfile target runner;
│   │                          #   _collect_targets() finds make/just targets in directory;
│   │                          #   QProcess output in QPlainTextEdit; split list + output view
│   ├── terminal_panel.py   # TerminalPanel (QWidget) — embedded QProcess terminal;
│   │                        #   start(cwd, *, selected, cursor): injects BIOME_CWD, BIOME_SELECTED
│   │                        #   (newline-joined), BIOME_CURSOR into QProcessEnvironment before launch;
│   │                        #   OSC7 escape tracking for cwd sync; default_shell() picks $SHELL or /bin/sh
│   ├── s3_versions_dialog.py # S3VersionsDialog(path, versions, parent) — S3 object versioning browser;
│   │                          #   QTableWidget (4 cols: Version ID / Last Modified / Size / Latest);
│   │                          #   restore_requested Signal(version_id: str) on "Restore This Version";
│   │                          #   versions: list[dict] with VersionId/LastModified/Size/IsLatest keys
│   ├── gallery_view.py     # ThumbnailLoader: ThreadPoolExecutor(max_workers=4) + SimpleQueue drain;
│   │                        #   request(path, callback) → QPixmap | None; background _load reads bytes;
│   │                        #   drain() scales to 128×128 (KeepAspectRatio, Smooth); dict cache 500-LRU;
│   │                        #   GalleryView (QWidget): QListView in IconMode + ThumbnailLoader;
│   │                        #   set_items(items) populates QStandardItemModel; 50ms QTimer drains; F404
│   ├── omnibar.py          # OmniBar (QFrame, Popup): Spotlight-style command palette overlay;
│   │                        #   QLineEdit + QListWidget; 150ms debounce QTimer → OmnibarPresenter.query_changed();
│   │                        #   activate(root) shows popup; navigated/command_chosen/search_chosen Signals;
│   │                        #   prefix / → navigate, > → command, bare text → search; F411
│   ├── dry_run_dialog.py   # DryRunDialog(cmd, history) — operation preview before execution;
│   │                        #   renders cmd.preview() → list[str] in QListWidget;
│   │                        #   Ok → CommandHistory.execute(cmd); Cancel dismisses; F442
│   ├── compare_panel.py  # CompareModel(QAbstractTableModel) + ComparePanel(QWidget) — directory comparison view;
│   │                        #   left/right columns with sync signals; diff_requested Signal(left, right) (F453)
│   ├── toolbar.py        # CustomToolBar (QToolBar) — user-configurable tool bar;
│   │                        #   actions populated from CommandRegistry entries; toolbar_actions Config list (F455)
│   ├── toolbar_builder_dialog.py # ToolbarBuilderDialog — drag-and-drop toolbar action editor;
│   │                              #   shows all registry commands (left list) + current toolbar (right list);
│   │                              #   Add/Remove/Move Up/Move Down; emits accepted_actions Signal(list[str]) (F455)
│   └── theme.py          # TOML-based theme system; load_theme(name) resolves plugin hook
│                          #   → TOML inheritance (meta.inherits) → _DARK_FALLBACK;
│                          #   _find_theme(): user AppConfig/biome-fm/themes/ first, then
│                          #   importlib.resources; _apply_palette() maps 10 tokens to QPalette;
│                          #   apply_theme(app, name, plugin_manager) publishes ThemeChanged;
│                          #   _TOKENS alias kept for backward compat; Template(_QSS_TMPL) fills QSS;
│                          #   glass opacity: _opacity_to_alpha(pct) → int; _apply_glass_alpha(tokens,
│                          #   opacity_pct=47) converts surface/surface2 to rgba(), preserves originals
│                          #   as surface_opaque/surface2_opaque (used by QMenu); selection alpha =
│                          #   surface alpha + 20; $surface_opaque token in QSS keeps QMenu opaque
│
├── commands/
│   ├── base.py           # Command ABC (execute/undo/undoable/preview) + CommandHistory (50 levels);
│   │                     #   preview() → list[str]: default returns [description]; subclasses
│   │                     #   override for per-path action strings used by DryRunDialog (F442);
│   │                     #   CommandHistory.push(cmd) records already-executed cmd for undo
│   ├── registry.py       # CommandRegistry + CommandEntry (name, shortcut, callback);
│   │                     #   record_hit(name) increments hit count; get_entry(name) → CommandEntry;
│   │                     #   search(query) returns entries sorted by hit count descending
│   ├── copy_cmd.py       # CopyCmd (shutil.copy2);
│   │                     #   ProgressCopyCmd: 256KB-chunk copy with cancel (threading.Event)
│   │                     #   + report(files_done, files_total, bytes_done, bytes_total, name);
│   │                     #   raises Cancelled on cancel.is_set(); undo deletes created files;
│   │                     #   _copy_cross_vfs: streams via vfs.open_read(path, offset) — resumes
│   │                     #   partial downloads by seeking to existing dst file size;
│   │                     #   calls vfs.utime(dst, src_mtime) after transfer to preserve timestamp
│   ├── move_cmd.py       # MoveCmd;
│   │                     #   ProgressMoveCmd: same cancel + report API, wraps shutil.move
│   ├── delete_cmd.py     # DeleteCmd (send2trash)
│   ├── rename_cmd.py     # RenameCmd
│   ├── mkdir_cmd.py      # MkdirCmd
│   ├── multi_rename_cmd.py # MultiRenameCmd (batch with pattern/counter)
│   ├── editor_rename_cmd.py # EditorRenameCmd — opens $EDITOR with names in tmp file;
│   │                        #   diffs old vs new names, applies RenameCmd per changed line; undoable
│   ├── export_listing_cmd.py # ExportListingCmd — writes current dir listing to .txt or .csv;
│   │                         #   fields: name, size, modified ISO timestamp; not undoable
│   ├── new_file_cmd.py     # NewFileCmd(path, content=b"") — creates file, undo=unlink; undoable
│   ├── symlink_cmd.py      # SymlinkCmd(target, link) — symlink_to; undo=unlink; undoable;
│   │                        #   HardlinkCmd(target, link) — os.link; undo=unlink; undoable
│   ├── trash_cmd.py        # TrashCmd(paths) — send2trash per path; not undoable;
│   │                       #   graceful degradation: warns + unlink if send2trash unavailable
│   ├── chmod_cmd.py        # ChmodCmd(paths, mode, recursive, vfs) — batch os.chmod with undo;
│   │                        #   saves previous mode per path; delegates to vfs.chmod if available;
│   │                        #   POSIX-only; undoable
│   ├── chown_cmd.py        # ChownCmd(paths, uid, gid) — batch os.chown with undo;
│   │                        #   saves (path, old_uid, old_gid) per file; raises NotImplementedError
│   │                        #   on Windows; POSIX-only; undoable
│   ├── remote_edit_cmd.py  # RemoteEditCmd(path, vfs, editor_cmd) — download→edit→re-upload;
│   │                        #   tempfile per suffix; re-uploads only if mtime changed; not undoable
│   ├── tag_cmd.py          # TagCmd(paths, add_tags, remove_tags, store) — batch tag assignment;
│   │                        #   saves previous tag list per path for undo; undoable
│   ├── archive_cmd.py      # ArchiveCmd(sources, archive_path, fmt) — create zip/tar.gz/tar.bz2;
│   │                        #   EncryptedArchiveCmd: calls `7z a -p<password>` subprocess for
│   │                        #   password-protected .7z creation; requires 7-Zip binary; undoable
│   ├── quarantine_cmd.py   # RemoveQuarantineCmd(paths) — removes com.apple.quarantine xattr;
│   │                        #   saves old xattr value per path for undo; undoable; macOS-only
│   ├── replace_cmd.py      # ReplaceCmd(path, query, replacement, regex=False) — in-place text replace;
│   │                        #   atomic write: .bak backup → .tmp write → rename; undoable via .bak restore;
│   │                        #   execute() → ReplaceResult(path, count, preview); uses _decode_content;
│   │                        #   search_replace(paths, query, replacement, regex, dry_run) batch helper
│   ├── rsync_cmd.py        # RsyncCmd(sources, dest_dir, cancel, report, extra_args) — Command subclass;
│   │                        #   delta-transfer via rsync subprocess (archive mode + progress parsing);
│   │                        #   cancel-safe: polls cancel.is_set() between sources, SIGTERM on cancel;
│   │                        #   undo deletes created destination files; rsync_available() guard;
│   │                        #   extra_args passthrough (e.g. --checksum, --exclude)
│   └── batch_exec_cmd.py   # BatchExecCmd(template, paths, cancel, on_progress) — run shell template
│                            #   on each selected file; not undoable;
│                            #   expand_template(template, path) replaces {f}=path, {n}=stem,
│                            #   {e}=ext, {d}=parent; cancel-safe (threading.Event); F412
│
├── git/
│   ├── status_cache.py     # GitStatusCache — TTL=10s dict[repo_path → RepoStatus];
│   │                       #   thread-safe (RLock); find_repo(path) walks to .git;
│   │                       #   RepoStatus(statuses: dict[Path, XY_code], dirty_dirs, fetched_at);
│   │                       #   invalidate(repo) clears cache entry for forced refresh
│   ├── worker.py           # GitStatusWorker (QObject) — fetches git status off main thread;
│   │                       #   request(dir_path): deduplicates by repo, submits to ThreadPoolExecutor;
│   │                       #   100ms QTimer drains queue.SimpleQueue → emits status_ready(RepoStatus)
│   ├── branch_ops.py       # Pure-Python git branch ops (no Qt);
│   │                       #   list_branches(repo) → list[str]; current_branch(repo) → name |
│   │                       #   '(detached)' | '' on error; switch_branch(repo, branch) raises
│   │                       #   RuntimeError on dirty tree or timeout
│   ├── commit_ops.py       # Pure-Python git staging/commit (no Qt);
│   │                       #   stage_files/unstage_files(repo, paths); staged_files(repo) → list[str];
│   │                       #   staged_diff(repo) → str — full staged diff via git diff --cached;
│   │                       #   commit(repo, message) → short hash; raises ValueError (empty msg)
│   │                       #   or RuntimeError on git failure
│   ├── virtual_pane.py     # git_changed_files(repo, cache) → list[FileItem];
│   │                        #   builds virtual pane from all dirty paths in repo via GitStatusCache
│   ├── worktree_ops.py     # list_worktrees(repo) → list[dict{path,head,branch}];
│   │                        #   parses `git worktree list --porcelain`; timeout-safe
│   └── conflict_ops.py     # ConflictMarker(line, marker, label) frozen dataclass;
│                            #   ConflictRegion(start, separator, end, ours, theirs) dataclass;
│                            #   conflicted_files(repo) → list[str] (git diff --diff-filter=U);
│                            #   find_conflict_markers(path) → list[ConflictMarker];
│                            #   parse_conflict_regions(path) → list[ConflictRegion]
│
├── operations/
│   ├── queue.py          # OpQueue: asyncio + ThreadPoolExecutor;
│   │                     #   submit(cmd, cancel, task_id) — accepts external cancel Event;
│   │                     #   next_task_id() / put_event() for async path in ManagerPresenter;
│   │                     #   _run() catches Cancelled → emits OpCancelled
│   └── task.py           # OpTask: priority, cancel (threading.Event), progress callback;
│                         #   Cancelled exception (raised inside Command to signal cancellation);
│                         #   OpStarted, OpProgress(task_id, files_done, files_total,
│                         #     bytes_done, bytes_total, current_file),
│                         #   OpDone, OpError, OpCancelled;
│                         #   OpEvent = union of all above
│
├── preview/
│   ├── provider.py       # PreviewProvider Protocol (priority, can_handle, render);
│   │                     #   ContentKind enum (IMAGE/TEXT/HTML/MARKDOWN/ERROR);
│   │                     #   PreviewRequest(path, dark); PreviewResult(kind, data, title)
│   ├── registry.py       # PreviewRegistry: sorted list[PreviewProvider] by priority;
│   │                     #   find(path) → first match or FallbackProvider()
│   ├── presenter.py      # PreviewPresenter (Qt-free): ThreadPoolExecutor(max_workers=1);
│   │                     #   64-item LRU cache keyed (path, mtime, dark) with 60s monotonic TTL;
│   │                     #   cache stores (PreviewResult, timestamp) tuples; stale entries re-fetch;
│   │                     #   queue.SimpleQueue for thread→main delivery; drain() polled by QTimer;
│   │                     #   toggle_item(), update_if_visible(), set_dark(), shutdown();
│   │                     #   set_tail_mode(enabled) — when True, auto-scrolls to end after each render
│   └── providers/
│       ├── image.py      # ImagePreviewProvider (priority=0); jpg/png/gif/webp/svg etc; 50MB limit
│       ├── markdown.py   # MarkdownPreviewProvider (priority=5); .md/.markdown/.mdx; 200KB limit;
│       │                 #   calls preview/markdown_renderer.render(md, dark, code_alpha) → HTML;
│       │                 #   rendering runs on main thread (Qt requirement); returns ContentKind.HTML
│       ├── code.py       # CodePreviewProvider (priority=8); Pygments syntax highlighting;
│       │                 #   get_lexer_for_filename() to detect language; skips TextLexer (falls
│       │                 #   through to TextPreviewProvider); monokai dark / friendly light;
│       │                 #   @lru_cache(maxsize=2) HtmlFormatter; 512KB limit; ContentKind.HTML
│       ├── text.py       # TextPreviewProvider (priority=10); .py/.js/.toml/.json etc; 256KB limit
│       ├── fallback.py   # FallbackProvider (priority=999); always handles; returns HTML metadata
│       ├── _git_helpers.py # Shared git helpers: find_repo(path) → Path | None (walks .git);
│       │                   #   run_git(args, cwd, timeout=5) → stdout str; raises on error
│       ├── git_blame.py  # GitBlamePreviewProvider (priority=2); any file in a git repo;
│       │                 #   runs `git blame --porcelain`, renders per-line commit+author HTML table
│       ├── git_log.py    # GitLogPreviewProvider (priority=2); any file in a git repo;
│       │                 #   runs `git log --oneline -50`, renders via Pygments TextLexer
│       ├── script.py     # ScriptPreviewProvider + ScriptSpec(extensions, command, priority);
│       │                 #   load_script_providers(dir) reads *.toml to build providers;
│       │                 #   command uses %f placeholder for file path; 5s timeout
│       ├── sqlite_preview.py # SqlitePreviewProvider (priority=5); .db/.sqlite/.sqlite3;
│       │                     #   opens read-only (URI mode); lists up to 5 tables × 20 rows as HTML
│       ├── csv_preview.py    # CsvTableProvider (priority=6); .csv/.tsv; 10MB limit; 50 row cap;
│       │                     #   _detect_delim() sniffs ,/;/tab from first 4KB; renders HTML table
│       ├── dotenv.py         # EnvFileProvider (priority=8); .env and .env.* files;
│       │                     #   masks values with *** via regex (KEY=*** format); returns TEXT kind
│       ├── json_tree.py      # JsonTreeProvider (priority=5); .json/.xml/.yaml/.yml/.toml; 512KB limit;
│       │                     #   collapsible HTML <details> tree; YAML needs pyyaml (falls back to TEXT);
│       │                     #   XML via stdlib ET; TOML via tomllib/tomli
│       ├── notebook.py       # NotebookProvider (priority=4); .ipynb; 4MB limit;
│       │                     #   renders code/markdown/raw cells + first 10 output lines as HTML;
│       │                     #   no nbconvert dependency — pure JSON parse
│       └── office.py         # OfficeProvider (priority=3); .docx/.xlsx/.pptx; 2MB limit;
│                             #   requires optional: python-docx, openpyxl, python-pptx;
│                             #   _docx: paragraph text; _xlsx: first 50 rows as table;
│                             #   _pptx: text per slide with slide numbers
│
├── themes/
│   ├── _base.qss.tmpl    # string.Template QSS; uses $base $surface $accent etc (10 tokens)
│   ├── dark.toml         # [meta] name=Dark; [tokens] 10 macOS system-color values
│   ├── light.toml        # [meta] name=Light; [tokens] 10 light-mode values
│   ├── catppuccin-mocha.toml  # third-party palette example
│   ├── high-contrast.toml    # [meta] inherits=dark; accent=#FFFF00, accent2=#00FFFF,
│   │                         #   border=#FFFFFF, text=#FFFFFF on base=#000000
│   └── colorblind-dark.toml  # [meta] inherits=dark; Okabe-Ito palette overrides:
│                              #   red=#E69F00 (orange), green=#0072B2 (blue);
│                              #   safe for deuteranopia/protanopia/tritanopia
│
├── plugins/
│   ├── types.py          # ThemeTokens (TypedDict, 14 keys — 10 base + 4 glass extras:
│   │                     #   base_bg, surface_opaque, surface2_opaque, selection_bg);
│   │                     #   _DARK_FALLBACK: ThemeTokens — canonical dark fallback, no Qt dep
│   │                     #   (moved here from views/theme.py so plugins/ stays view-free);
│   │                     #   ActionSpec dataclass (label, callback, shortcut, icon_name,
│   │                     #   separator_before); ColumnDef dataclass (id, title, width, alignment)
│   ├── hookspecs.py      # pluggy @hookspec: register_commands (historic=True),
│   │                     #   on_navigate(path), on_file_operation(op,src,dst),
│   │                     #   provide_theme(name) firstresult → ThemeTokens | None,
│   │                     #   before_file_operation(op,src,dst) firstresult → bool | None,
│   │                     #   context_menu_actions(items,pane_id) → list[ActionSpec],
│   │                     #   extra_columns() → list[ColumnDef],
│   │                     #   column_value(item, column_id) firstresult → str | None,
│   │                     #   extra_archive_extensions() → list[str],
│   │                     #   provide_vfs(path) firstresult → VFS | None,
│   │                     #   provide_preview_providers() → list[PreviewProvider]
│   │                     #   (plugins contribute PreviewProvider instances)
│   ├── manager.py        # PluginManager: API_VERSION=(1,0); register_plugin() checks
│   │                     #   BIOME_FM_API_VERSION major; load_entry_points() via
│   │                     #   importlib.metadata group='biome_fm.plugins';
│   │                     #   load_local_plugins(plugin_dir) — if None returns [] (caller
│   │                     #   must resolve path, avoids Qt import in plugins/); app.py passes
│   │                     #   QStandardPaths result; each .py must have top-level Plugin class;
│   │                     #   get_installed_plugins() → list[dict]; no Qt imports
│   ├── theme_registry.py # ThemeRegistry(pm): resolve(name) → _DARK_FALLBACK (from
│   │                     #   plugins/types.py) merged with plugin hook result (provide_theme
│   │                     #   firstresult); no Qt imports
│   └── builtin/
│       ├── __init__.py
│       └── dark_theme.py # BuiltinDarkTheme: BIOME_FM_API_VERSION=(1,0);
│                         #   provide_theme("dark") → _DARK_FALLBACK copy (imported from
│                         #   plugins/types.py); None for other names
│
├── ai/
│   ├── __init__.py       # Package init
│   ├── provider.py       # AIProviderProtocol (runtime-checkable) + NoOpProvider +
│   │                     #   make_providers(cfg) → dict[str, AIProviderProtocol];
│   │                     #   includes make_cli_providers() via ai/cli/backend_def
│   ├── claude_provider.py # ClaudeProvider (anthropic SDK, chat + chat_stream)
│   ├── openai_provider.py # OpenAIProvider (openai SDK, chat + chat_stream)
│   ├── ollama_provider.py # OllamaProvider (HTTP API, chat + chat_stream)
│   ├── types.py          # FileContent, ImageContent dataclasses for attachments
│   └── cli/              # CLI-tool AI providers (subprocess.Popen, no SDK dependency)
│       ├── backend_def.py # BackendDef frozen dataclass (name, cmd, models, prompt_fmt);
│       │                  #   CLAUDE_CODE / CODEX / OPENCODE constants;
│       │                  #   make_cli_providers() → dict keyed by name, only found binaries
│       ├── cli_provider.py # CliProvider: AIProviderProtocol via Popen; chat/chat_stream;
│       │                  #   resolve_binary() → Path | None; generator.close() → proc.terminate()
│       └── stream_parse.py # Line normalizers: parse_claude_code_line / parse_codex_line /
│                           #   parse_plain_line → str | None (skip control/JSON lines)
│
├── cli/                  # CLI installer (no Qt dependency)
│   ├── cli.py            # dispatch(argv) → int | UNHANDLED; subcommands:
│   │                     #   configure (auto/--client KEY), doctor, version, uninstall;
│   │                     #   UNHANDLED sentinel object for __main__ fallthrough
│   ├── clients.py        # ClientInfo(name, config_path, fmt); CLIENT_REGISTRY dict (8 clients:
│   │                     #   claude-code, claude-desktop, cursor, windsurf, vscode,
│   │                     #   opencode, codex, kimi); detect_installed() → list[str]
│   ├── merger.py         # merge_config/remove_entry for JSON clients;
│   │                     #   merge_toml_config/remove_toml_entry for TOML clients;
│   │                     #   atomic writes via temp file + rename
│   ├── resolver.py       # find_server_command() → list[str] (uvx > venv > python -m);
│   │                     #   build_server_entry() → dict ready for client config injection
│   └── automator.py      # generate_quick_action() → shell script str;
│                          #   install_quick_action() → ~/Library/Services/Open in Biome FM.workflow;
│                          #   no-op on non-macOS; biome-fm install-service CLI subcommand
│
├── ipc/                  # External IPC control interface (no SDK dep) — F409
│   ├── server.py         # IPCServer (QObject): QLocalServer on socket name "biome-fm";
│   │                     #   start() / stop(); _on_connection() reads JSON payload;
│   │                     #   publishes IPCCommandReceived(payload) to EventBus
│   ├── client.py         # send_command(payload, timeout=2.0) — stdlib AF_UNIX client;
│   │                     #   Qt-free; not supported on Windows (raises NotImplementedError)
│   └── rest_server.py    # RestAPIServer — stdlib HTTPServer in daemon thread; Bearer token auth;
│                         #   POST dispatches JSON payload to EventBus as IPCCommandReceived;
│                         #   start() → int (actual port, supports port=0 auto-assign) (F445)
│
├── scripting/             # Python scripting engine — exec user scripts with sandboxed context (F440)
│   ├── __init__.py
│   ├── context.py        # BiomeContext — scripting API injected as `biome` in exec namespace;
│   │                     #   wraps PanePresenter + CommandRegistry;
│   │                     #   navigate(path), execute(command_id), current_path, selected → list[Path]
│   └── engine.py         # ScriptingEngine(context) — exec() runner;
│                         #   exec_code(source) → None; ScriptError wraps SyntaxError/Exception
│
└── utils/
    ├── platform.py       # IS_MAC / IS_WIN / IS_LINUX; quick_look(path), quick_look_item(item),
    │                     #   reveal_in_finder(path), get_modifier_name() — cross-platform
    │                     #   (macOS: qlmanage -p / open -R; Windows: explorer /select; Linux: xdg-open);
    │                     #   share_files(paths) — opens macOS Share Sheet via `open --share`;
    │                     #   no-op on non-macOS or empty list
    ├── opener.py         # open_file(path) — default app opener (macOS: open, Win: os.startfile,
    │                     #   Linux: xdg-open); guards against virtual archive paths (path.exists()
    │                     #   check → set_status instead of show_error); passed to TabsPresenter as opener=
    ├── encoding.py       # detect_encoding(data) → str (chardet if available, else "utf-8");
    │                     #   decode_smart(data) → (text, enc_name); never raises;
    │                     #   normalize_filename(name) → str — NFC normalization via unicodedata
    │                     #   (reconciles macOS NFD filenames with Linux NFC)
    ├── panelize.py       # parse_shell_output(stdout, cwd) → list[FileItem];
    │                     #   parses stdout lines as paths; resolves relative to cwd; skips non-existent
    ├── global_hotkey.py  # register_global_hotkey(key_combo, callback) → listener | None;
    │                     #   uses pynput.keyboard.GlobalHotKeys; returns None if pynput absent
    ├── path_completion.py # path_completions(text) → sorted list of glob matches;
    │                       #   handles absolute (/…), tilde (~…), relative (./…) prefixes
    ├── touch_bar.py       # setup_touch_bar(window, actions) — macOS Touch Bar integration;
    │                       #   actions: list[tuple[label, callback]]; deferred import of _touch_bar_impl;
    │                       #   no-op guard on non-darwin or missing pyobjc (F452)
    └── transfer_stats.py # TransferStats — EWMA-smoothed (α=0.3) transfer speed tracker (no Qt);
                          #   update(t, bytes_done, bytes_total); speed_bps() → float; eta_seconds();
                          #   format_speed(bps) → "1.2 MB/s"; format_eta(secs) → "2m 30s"
```

## Patterns

### Hybrid Supervising Controller (MVP variant)
Views emit signals → Presenters react → update Models → push state to Views.
Views NEVER import models. Presenters have ZERO Qt imports — testable with plain Python mocks.
Model is a thin data adapter (QAbstractTableModel wrapping list[FileItem]).

### Command + Undo
Every file mutation = Command(execute + undo). CommandHistory (50 levels).
CommandRegistry maps string ids to callables for CommandPalette dispatch.
ManagerPresenter wires undo/redo to CommandHistory + refresh_both().

### VFS Host Chaining
VFSRouter walks path ancestry to detect archive roots (`.zip`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tgz`). `.7z` is explicitly excluded — unsupported by fsspec backend.
Matching paths → ArchiveVFS (stdlib `zipfile`/`tarfile`); plain paths → LocalVFS.
Nested archives supported via chained VFS instances; ArchiveVFS instances cached per root file.
`PanePresenter._is_archive()` triggers in-pane browsing on item activation.

### Plugin Hooks (pluggy)
Hookspecs: `register_commands` (historic), `on_navigate`, `on_file_operation`,
`before_file_operation`, `provide_theme` (firstresult), `context_menu_actions`,
`extra_columns`, `column_value` (firstresult), `extra_archive_extensions`.
Discovery: `importlib.metadata.entry_points(group="biome_fm.plugins")` + local
`~/.config/biome-fm/plugins/` scan. API versioning gates plugins on major version mismatch.
Builtin plugins live in `plugins/builtin/` and are registered in `create_app()`.

### Multi-Tab Panes
Each side (left/right) has a PaneSideView (QTabBar + QStackedWidget) driven by a TabsPresenter
owning N PanePresenters. Tabs persist to session.json via SessionState.
`_PathTabBar` (QTabBar subclass): middle-click or Ctrl+click copies full path from tooltip.
`_sync_tab_bar()` hides the tab bar entirely when single tab; shows it with close buttons when 2+ tabs.

### AI Integration (Multi-Model)
`AIProviderProtocol` with `chat()` and `chat_stream()` methods. Three providers:
`ClaudeProvider`, `OpenAIProvider`, `OllamaProvider`. `make_providers(cfg)` builds
available providers from config/env at startup; `NoOpProvider` fallback if none configured.
`AIChatPanel` composed of `ChatLog` (bubble-style HTML with streaming), `ContextBar`
(DnD file attachment chips), and model selector `QComboBox`. `AIPresenter` manages
active provider + model; streams tokens via `queue.SimpleQueue` → `QTimer` drain.
A 100ms QTimer drains the AI stream in `app.py`.

### Drag and Drop
`_PaneTableView` (inner class in pane_view.py) subclasses QTableView to override
`mimeData`/`startDrag`/`dragEnterEvent`/`dragMoveEvent`/`dragLeaveEvent`/`dropEvent`.
MIME type: `application/x-biome-fm-paths` (newline-joined absolute paths).
Folder highlight: `_DropHintDelegate` paints a 2px accent-colored rect around the row
stored in `_drop_hint_row`; `dragMoveEvent` sets it to the row under cursor if that
row is a non-`..` directory, or -1 otherwise; `dragLeaveEvent` clears it.
Drops emit `files_dropped(paths: list[Path], move: bool, target_folder: Path | None)`
on `PaneView`. `target_folder` is the hovered folder's path if dropping on a folder,
else None (drop goes to pane's current directory).
`app.py` wires this to `ManagerPresenter.drop_files(paths, target_pane_id, move, target_folder)`,
which resolves paths, filters same-dir no-ops, then dispatches ProgressCopyCmd or ProgressMoveCmd
via OpQueue (async path). `DirectoryModel.flags()` adds `ItemIsDragEnabled`.

### Active Pane Tracking
`app.py` tracks focus via `focusChanged` (QApplication signal).
The active `PaneSideView` receives `set_active(True)`, the inactive one `False`.
`set_active()` toggles QSS dynamic property `active`; `_base.qss.tmpl` applies a
3px left accent border + 1px top accent border (transparent borders of same width
for inactive pane to prevent layout shift).
`ManagerPresenter.set_active_pane(pane_id)` keeps the presenter layer in sync for
operations that target the opposite pane.
`ActivePaneChanged` event is published to the EventBus on every switch.

### Nav Bar
`PaneView` renders a nav bar above the table: `[◄ back] [► forward] [▲ up] [★ bookmark menu] | BreadcrumbBar(stretch) | [+ new tab]`.
Home button removed from nav bar (home_requested signal retained for keyboard shortcut).
`_btn_new_tab` (QPushButton) at the right emits `new_tab_requested`; wired per-pane in `app.py`
so each side creates tabs in its own panel. Buttons use `QStyle.StandardPixmap` icons with tooltips.

### Quick Filter
`/` key in `_PaneTableView` calls `parent.filter_bar.activate()`.
`FilterBar` is a hidden QLineEdit row in PaneView; `filter_changed` → `DirSortFilterProxy.set_filter()`.
Escape deactivates and clears the filter.

### Type-to-Navigate (JumpBar)
Any printable keystroke (not Ctrl/Alt modified, not Space) routes to `JumpBar.append_char()`.
`JumpBar` shows an overlay label with accumulated text, emits `jump_text_changed`.
`PaneView._on_jump()` scans proxy rows for the first name with matching prefix (case-insensitive).
Auto-clears after 600ms of inactivity.

### File-Type Coloring
`DirectoryModel.data(ForegroundRole)` returns a colored `QBrush` per extension group:
archives=orange, images=pink, code/scripts=green, docs=blue, media=yellow.
Hidden files (starting with `.`) are dimmed. Directories and `..` are unstyled.

### Sync Browsing
`ManagerPresenter.toggle_mirror()` toggles `_mirror` flag.
`navigate_active(path)` navigates the active pane; if mirror is on, also navigates the opposite pane.
Re-entrancy guard `_mirroring` prevents infinite loops.
Wired to `Ctrl+Shift+L` shortcut in `app.py`.

### Theme / Skins (v0.7.0)

Themes are TOML files with 10 named color tokens. A `string.Template` in
`themes/_base.qss.tmpl` is substituted at apply time to produce the full QSS.

`ThemeTokens` TypedDict keys (all 10): `base`, `surface`, `surface2`, `border`,
`text`, `text_dim`, `accent`, `accent2`, `red`, `green`.

```
apply_theme(app, name, plugin_manager)
      │
      ├─ plugin_manager.hook.provide_theme(name)  [firstresult]
      │        result merged over _DARK_FALLBACK
      │
      ├─ _find_theme(name):
      │        1. ~/.config/biome-fm/themes/<name>.toml      (user override)
      │        2. ~/.config/biome-fm/themes/<name>/theme.toml
      │        3. importlib.resources biome_fm.themes/<name>.toml  (bundled)
      │        4. None → _DARK_FALLBACK
      │
      ├─ TOML inheritance: [meta] inherits = "<parent>"
      │        cycle guard via _seen frozenset; child [tokens] override parent
      │
      ├─ _apply_palette(app, tokens)   ← 10 tokens → QPalette roles
      │        Disabled group: text + ButtonText → text_dim
      │
      ├─ app.setStyleSheet(Template(_QSS_TMPL).substitute(tokens))
      │
      └─ bus.publish(ThemeChanged(name=name, tokens=tokens))
```

Bundled themes: `dark`, `light`, `catppuccin-mocha`, `high-contrast`, `colorblind-dark`.
User themes: drop `<name>.toml` into `~/.config/biome-fm/themes/`.
`_TOKENS` and `_QSS` are backward-compat aliases in `theme.py`.

### Overlay / Detachable Panel System (v0.8.0)

Preview and AI panels open in the pane *opposite* the active one.
`PanelManager` (pure Python, no Qt) owns the state and produces `Effect` objects.
`PanelCoordinator` (QObject) consumes Effects and drives Qt widgets.

```
User presses Space/F3 (preview) or Ctrl+I (AI)
      │
      ▼
PanelCoordinator.toggle(name, active_side)
      │
      ▼
PanelManager.toggle(name, active_side) → list[Effect]
      │
      ├─ Effect(show_overlay, target_side=opposite)
      │       hide pane widget on opposite side (_hidden_widget)
      │       show panel widget in its place
      │       save splitter sizes
      │
      ├─ Effect(set_opposite_visible, False)
      │       replaces right pane when active=left, left pane when active=right
      │
      └─ Effect(show_floating) — via View → Detach Preview / Detach AI
              panel detached into QDialog; pane widget restored
```

States: `HIDDEN → OVERLAY → FLOATING` (and back). Each named panel tracks its own state.
Session: `PanelSession(overlay_side)` saved to `session.json` so overlay side survives restart.

### Preview System (v0.7.0)

`Space` / `F3` → `PreviewPresenter.toggle_item()` → slide-in `PreviewPanel` (350px, 150ms OutCubic).
Cursor move → `update_if_visible()` (no-op if panel hidden).

```
FileItem
      │  Space / cursor-move
      ▼
PreviewPresenter
      ├─ cache hit (path, mtime) → PreviewPanel.show_result()        [sync]
      └─ cache miss:
             PreviewRegistry.find(path) → PreviewProvider
             ThreadPoolExecutor (max_workers=1)
                   │  [background thread]
                   ▼
             PreviewProvider.render(PreviewRequest) → PreviewResult
                   │  queue.SimpleQueue.put(result)
             QTimer.drain() — main thread
                   ▼
             PreviewPanel.show_result(result)
                   match ContentKind:
                     IMAGE    → QLabel.setPixmap (KeepAspectRatio)
                     HTML     → QTextBrowser.setHtml
                     TEXT     → QTextBrowser.setPlainText
                     MARKDOWN → QTextBrowser.setMarkdown
                     ERROR    → QTextBrowser.setPlainText "Error: ..."
```

Provider priority (ascending = higher wins; first `can_handle` match used):

| Provider | Priority | Extensions / Condition | Limit |
|---|---|---|---|
| ImagePreviewProvider | 0 | jpg/png/gif/webp/svg/bmp/tiff/ico | 50 MB |
| GitBlamePreviewProvider | 2 | any file in git repo (mode: Blame) | — |
| GitLogPreviewProvider | 2 | any file in git repo (mode: Log) | — |
| OfficeProvider | 3 | .docx/.xlsx/.pptx | 2 MB |
| NotebookProvider | 4 | .ipynb | 4 MB |
| JsonTreeProvider | 5 | .json/.xml/.yaml/.yml/.toml | 512 KB |
| MarkdownPreviewProvider | 5 | .md/.markdown/.mdx/.mdown | 200 KB |
| SqlitePreviewProvider | 5 | .db/.sqlite/.sqlite3 | — |
| CsvTableProvider | 6 | .csv/.tsv | 10 MB |
| EnvFileProvider | 8 | .env / .env.* | — |
| CodePreviewProvider | 8 | Pygments-supported (not TextLexer) | 512 KB |
| TextPreviewProvider | 10 | .py/.js/.ts/.toml/.json + 20 more | 256 KB |
| ScriptPreviewProvider | 50 (default) | configured extensions (.toml spec) | — |
| FallbackProvider | 999 | * (always) | — |

Cache: 64 entries, key `(path, mtime, dark)`. Each entry stores `(PreviewResult, timestamp)`.
60s monotonic TTL — stale entries are re-fetched even on key match. FIFO eviction (oldest dropped when full).
`ThemeChanged` event → `PreviewPresenter.set_dark()` so next render picks correct palette.
`preview/markdown_renderer.render(md, dark, code_alpha=140)` is a Pygments-enhanced HTML path
(canonical location since architecture-review-fixes refactor; `models/markdown_renderer.py` is
now a backward-compat shim that re-exports from there).

### Plugin System Enhancements (v0.7.0)

10 hook specs; plugins implement any subset:

| Hook | Mode | Purpose |
|------|------|---------|
| `register_commands` | historic | Add CommandEntry to CommandRegistry at startup |
| `on_navigate` | broadcast | Pane navigated to path |
| `on_file_operation` | broadcast | Post-op notification (copy/move/delete/mkdir) |
| `provide_theme` | firstresult | Supply ThemeTokens for named theme |
| `before_file_operation` | firstresult | Veto op by returning False |
| `context_menu_actions` | broadcast | Inject ActionSpec items into context menu |
| `extra_columns` | broadcast | Inject ColumnDef into file listing |
| `column_value` | firstresult | Supply per-cell string value for a plugin column |
| `extra_archive_extensions` | broadcast | Register extra archive extensions |
| `provide_vfs` | firstresult | Supply a custom VFS for a given path prefix |
| `provide_preview_providers` | broadcast | Contribute `list[PreviewProvider]` instances |

Loading order in `create_app()`:
1. `load_entry_points()` — installed packages (`biome_fm.plugins` entry_points group)
2. `load_local_plugins()` — `.py` files / dirs with `__init__.py` in `~/.config/biome-fm/plugins/`
3. Builtin plugins — `BuiltinDarkTheme` registered last

API versioning: `BIOME_FM_API_VERSION = (1, 0)` on plugin class.
Major mismatch → `warnings.warn` + skip. Minor is backward-compatible.
Local plugin contract: must expose top-level `Plugin` class; loaded as `biome_fm_local_<stem>`.

`ThemeRegistry(pm).resolve(name)` = thin helper that calls `provide_theme` firstresult
hook then merges over `_DARK_FALLBACK`; used in `theme.py`'s `load_theme()`.

### Async File Operations with Progress + Cancel (v0.9.0)

`ManagerPresenter.drop_files()` dispatches through an async path via `OpQueue`:

```
drop_files(paths, target_pane_id, move, target_folder)
      │
      ├─ resolve dest_dir (target_folder or pane's cwd)
      ├─ cancel = threading.Event()
      ├─ task_id = queue.next_task_id()
      ├─ cmd = ProgressCopyCmd / ProgressMoveCmd
      │         (sources, dest_dir, vfs, cancel, _noop_report)
      ├─ queue.submit(cmd, cancel=cancel, task_id=task_id)
      │         ThreadPoolExecutor._run():
      │           cmd.execute() → 256KB chunks → cancel.is_set() → raise Cancelled
      │           Cancelled → put(OpCancelled)
      │           done      → put(OpDone)
      └─ publish(AsyncOpSubmitted(task_id, desc, cancel))
               ▼
         app.py._on_async_op()
               ▼
         ProgressDialog(task_id, desc, parent=window)
               │  Cancel button → cancel.set()
               │  OpProgress events → update bars
               └─ OpDone / OpCancelled → dialog.close()
```

`ProgressCopyCmd.execute()` copies source-by-source; `_copy_file()` reads in 256KB
chunks, checks `cancel.is_set()` each chunk (partial file deleted on cancel).
`ProgressMoveCmd` calls `shutil.move` per file (atomic on same FS, copy+delete otherwise).
Both support undo: `CommandHistory.push(cmd)` records the already-executed command
after successful completion so Ctrl+Z can reverse it.

### Settings Window (v0.9.0)

`SettingsPresenter` is Qt-free; `SettingsViewProtocol` is a structural Protocol with
`set_*/get_*` methods for each config field. `SettingsDialog` (4-tab QDialog) implements
the protocol. `app.py` wires `Ctrl+,` → `_open_settings()` which creates a
`SettingsDialog`, a `SettingsPresenter(cfg, dialog, bus, plugin_manager)`, calls
`presenter.load()`, shows the dialog, and on `Accepted` calls `presenter.save()`.
`save()` persists to TOML and publishes events (`ShowHiddenToggled`, `ThemeChanged`)
as needed so the live UI reflects changes immediately.

### Toggle Hidden Files (v0.9.0)

`Ctrl+H` → `ManagerPresenter.toggle_hidden()` → flips `Config.show_hidden` →
publishes `ShowHiddenToggled(enabled)`. `app.py` subscribes: `_on_show_hidden(ev)`
calls `proxy.set_show_hidden(ev.enabled)` on every `DirSortFilterProxy` (both panes,
all tabs). `DirSortFilterProxy.filterAcceptsRow()` rejects dotfile names when
`_show_hidden=False`. Setting persisted to config on next `save_config()` call.

### Breadcrumb Path Bar (v0.11.0)

`BreadcrumbBar` replaces the old `_PathComboBox` in `PaneView._path_bar`. It owns a
`QStackedWidget` with two children: `_CrumbRow` (breadcrumb mode) and `_PathComboBox`
(edit mode). Clicking any segment navigates there; clicking the edit zone or pressing
a nav shortcut switches to edit mode.

```
PanePresenter.set_path(path)
      │
      ▼
PaneView.set_path(path) → BreadcrumbBar.set_path(path)
      │
      ├─ path_segments(path) → [(label, full_path), ...]   [pure, no Qt]
      │
      └─ _CrumbRow._rebuild() → clears old buttons, creates one _SegmentButton per segment
               │  click segment
               ▼
         BreadcrumbBar.path_entered.emit(str(full_path))
               ▼
         PaneView._on_path_entered_text(text) → path_change_requested.emit(Path(text))
```

Horizontal wheel/swipe on `_CrumbRow`: `wheelEvent` accumulates `angleDelta().x()`;
when abs(delta) >= 120 and cooldown (300ms) elapsed → emits `back_requested` (delta < 0)
or `forward_requested` (delta > 0). Tracks macOS trackpad momentum without spurious
repeat triggers.

RMB context menu on any segment button: Copy Path / Copy Name / Show in Finder /
Open Terminal Here (calls `platform.open_terminal(segment_path)`).

`path_segments(path)` is a pure function in `breadcrumb_bar.py` — no Qt, fully unit-tested.

### CLI AI Providers (v0.11.0)

`ai/cli/` wraps external CLI tools as `AIProviderProtocol` implementations without
requiring any Python SDK. Three builtins: `CLAUDE_CODE` (`claude`), `CODEX` (`codex`),
`OPENCODE` (`opencode`).

```
make_cli_providers()
      │
      ├─ for each BackendDef in [CLAUDE_CODE, CODEX, OPENCODE]:
      │       BackendDef.resolve_binary() → which(cmd) → Path | None
      │       found → CliProvider(backend) added to result dict
      │
      └─ result merged into make_providers(cfg) output
```

`CliProvider.chat_stream(messages, system)`:
1. `_build_prompt(messages, system)` → plain-text prompt string
2. `_backend.build_argv(prompt, model)` → argv list
3. `subprocess.Popen(argv, stdout=PIPE, text=True)` → line iterator
4. Each line → `stream_parse.parse_*_line(line)` → str token | None
5. Yields non-None tokens; `generator.close()` → `finally: proc.terminate()`

`stream_parse.py` handles per-backend quirks: claude-code emits JSON SSE lines that
are filtered; codex emits plain text; opencode uses a different JSON schema.

### CLI Installer (v0.11.0)

`cli/` provides subcommands for registering biome-fm in AI tool client configs
(Claude Code, Cursor, VS Code, etc.) without importing Qt.

```
biome-fm configure          # dispatched in __main__.py before Qt import
      │
      └─ cli/cli.py::_configure(argv)
               │
               ├─ clients.detect_installed() → list of found client config files
               ├─ resolver.build_server_entry() → {"command": ..., "args": [...]}
               │       find_server_command():
               │           1. uvx run biome-fm   (preferred — isolated env)
               │           2. .venv/bin/biome-fm  (project venv)
               │           3. python -m biome_fm  (fallback)
               └─ merger.merge_config(info, entry)
                       JSON clients: atomic write via tmp file + os.replace
                       TOML clients: section merge
```
