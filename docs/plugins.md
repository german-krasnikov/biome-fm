# Plugin Authoring Guide

biome-fm uses [pluggy](https://pluggy.readthedocs.io/) for plugins. A plugin is a Python class
with `BIOME_FM_API_VERSION = (1, 0)` that implements any subset of the hook specs.

## Drop-in plugin (no packaging needed)

Drop a `.py` file in `~/.config/biome-fm/plugins/`:

```python
# ~/.config/biome-fm/plugins/my_plugin.py
from biome_fm.plugins.types import ActionSpec

class Plugin:
    BIOME_FM_API_VERSION = (1, 0)

    def context_menu_actions(self, items, pane_id):
        return [ActionSpec(label="Open in Obsidian", callback=lambda: ...)]
```

## Packaged plugin (entry_points)

```toml
# pyproject.toml
[project.entry-points."biome_fm.plugins"]
my_plugin = "my_plugin:Plugin"
```

## Available hooks

| Hook | Called when | Return |
|------|-------------|--------|
| `register_commands(registry)` | App startup | — |
| `on_navigate(path)` | Pane navigates | — |
| `on_file_operation(op, src, dst)` | After copy/move/delete/mkdir | — |
| `before_file_operation(op, src, dst)` | Before op (firstresult) | `False` to veto |
| `provide_theme(name)` | Theme load (firstresult) | `ThemeTokens` or `None` |
| `context_menu_actions(items, pane_id)` | Context menu open | `list[ActionSpec]` |
| `extra_columns()` | File list init | `list[ColumnDef]` |
| `extra_archive_extensions()` | VFS init | `list[str]` |
| `provide_vfs(path)` | Path navigation (firstresult) | VFS object or `None` |

## API versioning

Major version mismatch → plugin is skipped with a `warnings.warn`. Minor versions are backward-compatible.
Current API: `(1, 0)`.

---

## Lightweight extension points

The following extension points do **not** require the pluggy plugin system. They
are file-backed and loaded from `~/.config/biome-fm/` at startup.

### Preview Script Providers

Drop a TOML file in `~/.config/biome-fm/preview_scripts/` to add a custom preview
renderer for any file extension.

```toml
# ~/.config/biome-fm/preview_scripts/markdown.toml
extensions = [".md", ".markdown"]
command    = ["bat", "--color=always", "%f"]
priority   = 60   # higher wins; default 50
```

`%f` in `command` is replaced with the absolute path of the file being previewed.
The script's stdout is shown as plain text in the preview pane. Timeout: 5 s.

Loaded via `biome_fm.preview.providers.script.load_script_providers(dir)`.

### Custom File Associations

Maps file suffixes to applications. Stored as JSON at a path supplied at startup.

```json
// ~/.config/biome-fm/associations.json
{
  ".md": "/Applications/Obsidian.app",
  ".psd": "/Applications/Photoshop.app"
}
```

API (`biome_fm.models.associations.FileAssociations`):

| Method | Description |
|--------|-------------|
| `get(suffix)` | Returns app path or `None` |
| `set(suffix, app)` | Add/update mapping in memory |
| `save()` | Persist to JSON |

### User Actions / Context Menu

Add shell commands to the right-click context menu. Stored as JSON at a path
supplied at startup. Edit via **Tools → Menu Builder** (`MenuBuilderDialog`).

```json
// ~/.config/biome-fm/user_actions.json
[
  {
    "label": "Open in VS Code",
    "command": "code \"%f\"",
    "extensions": [".py", ".ts"]
  }
]
```

`extensions` filters visibility by file suffix. Empty list = shown for all files.

API (`biome_fm.models.user_actions.UserActionsStore`):

| Method | Description |
|--------|-------------|
| `add(action)` | Append a `UserAction` |
| `update(idx, action)` | Replace by index |
| `remove(idx)` | Delete by index |
| `actions_for(suffix)` | Actions matching suffix or with no filter |
| `save()` / `load()` | JSON persistence |

### Script Runner

Discovers and runs `.py` and `.sh` scripts from a directory.

```python
from biome_fm.models.script_runner import ScriptRunner

runner = ScriptRunner(Path("~/.config/biome-fm/scripts").expanduser())
for script in runner.list_scripts():
    result = runner.run(script, selected=[Path("/tmp/foo.txt")], cwd=Path("/tmp"))
    print(result.stdout)
```

Environment variables set on the child process:

| Variable | Value |
|----------|-------|
| `BIOME_SELECTED` | Newline-separated absolute paths of selected files |
| `BIOME_CWD` | Absolute path of the active pane directory |

Python scripts are run with the same interpreter as biome-fm (`sys.executable`).
Shell scripts are run directly (must be executable). Timeout: 30 s.
