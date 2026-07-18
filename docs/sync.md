# Directory Synchronization

Open the sync dialog from **Tools → Synchronize Directories** or `Ctrl+Shift+Y` (when both
panes are open). The left pane is the source; the right pane is the destination.

## Modes

| Mode | Behaviour |
|------|-----------|
| **Copy newer** (default) | Copies files where source is newer or destination is missing |
| **Mirror** | Makes destination an exact copy — files absent from source are deleted |
| **Dry run** | Preview only: shows what would change without touching anything |

Always run a dry run first when using Mirror mode.

## Exclude Patterns

Enter a comma-separated list of glob patterns to skip during sync:

```
*.pyc, __pycache__, .DS_Store, node_modules
```

Patterns are matched against the relative file path within the source tree.

## Conflict Detection

When a file exists in both source and destination and both are modified, biome-fm flags
it as a conflict. For each conflict you can choose:

- **Overwrite** — replace destination with source
- **Skip** — leave destination unchanged
- **Auto-rename** — copy source as `filename (2).ext`
- **Bulk action** — apply the same choice to all remaining conflicts

## Session Profiles

Sync configurations (source, destination, mode, excludes) can be saved as named profiles
and reloaded in future sessions. Profiles are stored in `~/.config/biome-fm/sync_profiles.toml`.

```toml
# ~/.config/biome-fm/sync_profiles.toml
[profiles.photos-backup]
source = "/Users/me/Pictures"
destination = "/Volumes/Backup/Pictures"
mode = "copy_newer"
excludes = [".DS_Store", "*.tmp"]
```
