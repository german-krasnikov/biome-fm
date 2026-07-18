# Search

Open the search dialog with `Ctrl+Shift+F`.

## Query Syntax

| Syntax | Meaning |
|--------|---------|
| `word` | Files whose names or content contain `word` |
| `foo bar` | Both `foo` AND `bar` must match (space = AND) |
| `-pattern` | Exclude files matching `pattern` |
| `"exact phrase"` | Literal phrase match |

## Options

| Option | Description |
|--------|-------------|
| Case sensitive | Match exact case (off by default) |
| Whole word | Match `foo` but not `foobar` |
| Archive search | Search inside zip / tar / 7z members |
| Context lines | Show N lines before/after each content match |

## Search Scope

The scope selector controls where biome-fm looks:

| Scope | Searches |
|-------|---------|
| Current directory | Top-level entries of the active pane only |
| Subtree | Active pane directory and all subdirectories |
| All open tabs | Every tab in both panes |

## Exclusion Patterns

Prefix any term with `-` to exclude files that match it:

```
*.log -node_modules -*.min.js
```

This finds all `.log` files but skips anything under `node_modules` or minified JS files.

## Archive Search

Enable **Archive search** to scan inside compressed files. biome-fm extracts members
to a temporary location and searches their text content. Supported formats: zip, tar,
tar.gz, tar.bz2, tar.xz, 7z, rar.

## Search Results Pane

Results open in a virtual pane. Keyboard shortcuts work normally — press `F5` to copy
a result to the other pane, `Enter` to open it, `F3` to preview.
