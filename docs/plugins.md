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

## API versioning

Major version mismatch → plugin is skipped with a `warnings.warn`. Minor versions are backward-compatible.
Current API: `(1, 0)`.
