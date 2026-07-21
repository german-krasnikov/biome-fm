# Keyboard Shortcuts

## Navigation

| Key | Action |
|-----|--------|
| `Enter` / `Return` | Open file / enter directory |
| `Backspace` / `Alt+Up` | Go up one directory |
| `Alt+Left` / `Alt+[` | Back |
| `Alt+Right` / `Alt+]` | Forward |
| `Alt+Home` | Go to home directory |
| `Tab` | Switch active pane |
| `/` | Quick filter |
| (printable) | Type-to-navigate (JumpBar) |
| `Ctrl+P` | Command palette / fuzzy finder |
| `Ctrl+J` | Frecency jump dialog (recent directories) |
| `Ctrl+D` | Toggle bookmark for current path |
| `Alt+B` | Open bookmarks dialog |
| `Ctrl+1`–`Ctrl+9` | Jump to numbered bookmark |
| `Alt+Ctrl+1`–`Ctrl+9` | Assign current path to numbered bookmark |
| `Alt+C` | Quick CD — frecency + path-completion jump dialog |

### Path Yank (leader sequences — press `y` then the second key)

| Sequence | Copies to clipboard |
|----------|---------------------|
| `y n` | File name only |
| `y p` | Full absolute path |
| `y d` | Parent directory |
| `y e` | File extension |

## File Operations

| Key | Action |
|-----|--------|
| `F5` | Copy selected to other pane |
| `F6` | Move selected to other pane |
| `F7` | Create directory |
| `F8` | Delete selected |
| `F9` | Inline rename |
| `Insert` | Mark item and advance cursor |
| `Delete` | Move selected to trash |
| `Shift+Delete` | Permanently delete selected |
| `Ctrl+C` | Copy selected to clipboard |
| `Ctrl+X` | Cut selected to clipboard |
| `Ctrl+V` | Paste from clipboard |
| `Ctrl+Z` | Undo last operation |
| `Ctrl+Shift+Z` | Redo |
| `Ctrl+Shift+R` | Bulk rename (multi-file editor) |
| `Ctrl+.` | Repeat last file operation |
| `Alt+Return` | File properties (info panel) |
| `Alt+Shift+N` | Copy file names to clipboard |

### Collections

| Key | Action |
|-----|--------|
| `Ctrl+Alt+C` | Add selection to collection |
| `Ctrl+Alt+V` | Show collection |

## View & Panels

| Key | Action |
|-----|--------|
| `Space` / `F3` | Toggle preview panel |
| `F4` | Open current file in editor |
| `F11` | Fullscreen preview viewer |
| `Ctrl+I` | Toggle AI chat panel |
| `Ctrl+`` ` | Toggle embedded terminal |
| `Ctrl+H` / `Ctrl+Shift+.` | Toggle hidden files |
| `Ctrl+Shift+L` | Toggle sync browsing |
| `Ctrl+T` | New tab |
| `Ctrl+Alt+T` | Duplicate tab |
| `Ctrl+W` | Close tab / close built-in editor |
| `Ctrl+R` | Refresh |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+Shift+T` | Toggle flat view / Open storage treemap ⚠ |
| `Ctrl+Shift+U` | Mirror active pane path to inactive pane |
| `Ctrl+=` / `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |
| `Ctrl+Shift+M` | Open task runner |
| `Ctrl+Shift+D` | Duplicate file finder |

> ⚠ `Ctrl+Shift+T` is bound to both "Toggle flat view" and "Open storage treemap" in source — both will fire (Qt ambiguous shortcut). Fix pending.

## Preview / Editor

| Key | Action |
|-----|--------|
| `R` | Rotate image (image preview) |
| `Ctrl+Wheel` | Zoom in / out (image preview) |
| `Ctrl+S` | Save file (built-in editor) |

## Search & Select

| Key | Action |
|-----|--------|
| `Ctrl+Shift+F` | Global search |
| `Ctrl+Shift+N` | Natural-language file operation |
| `Ctrl+G` | Select / deselect by pattern |
| `Ctrl+Shift+G` | Select by criteria (size, date, type) |
| `Shift+Down` | Mark item and advance cursor |
| `Shift+Up` | Mark item and retreat cursor |

## Sessions

| Key | Action |
|-----|--------|
| `Ctrl+Shift+S` | Save named session |
| `Ctrl+Shift+O` | Open session picker |

## Settings & App

| Key | Action |
|-----|--------|
| `Ctrl+,` | Open settings |
| `Ctrl+Shift+C` | Copy current path to clipboard |
| `Ctrl+Shift+P` | Fuzzy file finder / Set permissions ⚠ |
| `Ctrl+Shift+Y` | Synchronize directories |
| `Ctrl+U` | Swap panes |
| `F1` / `?` | Show shortcut help |
| `F2` | Open user menu (configured in `commands.toml`) |

> ⚠ `Ctrl+Shift+P` is bound to both "Fuzzy file finder" and "Set permissions" in source — both will fire (Qt ambiguous shortcut). Fix pending.
>
> `Ctrl+Shift+L` is bound to both "Toggle sync browsing" and "Large file finder" — Qt ambiguous shortcut. Fix pending.
