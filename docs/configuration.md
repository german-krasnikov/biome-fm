# Configuration

biome-fm stores its configuration in `~/.config/biome-fm/config.toml`.
Open the settings dialog with `Ctrl+,` or edit the file directly.

## Config Backup

Every save creates a rolling backup: `config.toml.bak.1` through `config.toml.bak.7`.
Backup 1 is always the most recent. Old backups rotate out automatically.

## Key Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `diff_tool` | string | `""` | External diff command (e.g. `"opendiff %a %b"`). `%a`/`%b` are replaced with the two files. |
| `theme` | string | `"dark"` | Base theme: `"dark"` or `"light"`. Overridden by `follow_system_theme` when true. |
| `follow_system_theme` | bool | `true` | Track the OS light/dark theme automatically |
| `editor_cmd` | string | `""` | External editor command for `F4`. Empty = built-in editor |
| `show_git_status` | bool | `true` | Show git XY status column in file list |
| `auto_preview` | bool | `true` | Auto-open preview on cursor move |
| `hidden_columns` | list | `[]` | Column names to hide (`"Size"`, `"Modified"`, `"Ext"`, `"Git"`) |
| `show_hidden` | bool | `false` | Show hidden files and directories (dotfiles) |
| `file_type_colors` | bool | `true` | Colorize file entries by type/extension |
| `sync_browsing` | bool | `false` | Mirror navigation across both panes simultaneously |
| `serial_ops` | bool | `false` | Run copy/move operations sequentially instead of in parallel |
| `highlight_rules` | list | `[]` | Custom highlight rules (list of `{pattern, color}` dicts) |
| `global_hotkey` | string | `""` | System-wide hotkey to bring biome-fm to focus (e.g. `"<ctrl>+<alt>+b"`) |

## Opener Rules

Map glob patterns to applications in `~/.config/biome-fm/opener_rules.toml`:

```toml
[[rules]]
pattern = "*.md"
command = ["obsidian", "%f"]
priority = 10

[[rules]]
pattern = "*.{jpg,png,gif}"
command = ["open", "-a", "Preview", "%f"]
priority = 5
```

`%f` is replaced with the absolute file path. Higher `priority` wins when multiple rules match.
Opener rules take precedence over system default associations.

## Glass / Acrylic Background

Enable a translucent window background:

```toml
glass = true
glass_opacity = 47   # 0 (fully transparent) – 100 (opaque)
```

Has no effect on platforms or compositors that do not support transparency.

## Column Visibility

Toggle columns via `Ctrl+Shift+Y` or by adding them to `hidden_columns`:

```toml
hidden_columns = ["Ext", "Git"]
```

Visibility is applied per-pane and persisted across sessions.

## Toolbar

The custom toolbar sits below the menu bar and shows quick-access action buttons.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `toolbar_visible` | bool | `false` | Show the custom toolbar |
| `toolbar_actions` | list[str] | `[]` | Ordered list of action IDs to display as toolbar buttons |

Action IDs match the string keys registered in the `ActionRegistry` (e.g. `"new_folder"`, `"copy"`, `"move"`, `"delete"`, `"terminal_here"`). Use `"---"` as a separator.

```toml
toolbar_visible = true
toolbar_actions = ["new_folder", "---", "copy", "move", "delete"]
```

## Remote / URI Navigation

Type a URI in the breadcrumb bar to connect:

| URI scheme | Protocol |
|-----------|---------|
| `sftp://user@host/path` | SSH file transfer |
| `s3://bucket/prefix` | Amazon S3 (requires `s3fs` or `fsspec[s3]`) |
| `ftp://host/path` | FTP |
| `webdav://host/path` | WebDAV |

Credentials for SFTP/FTP are prompted on first connect and cached in the session keychain.

## Cloud Profiles

Named cloud connections are stored in `~/.config/biome-fm/cloud_profiles.toml`. Edit via
**Tools → Cloud Profiles** or the `CloudProfileDialog`.

```toml
[profiles.my-s3]
scheme = "s3"
host   = "my-bucket.s3.us-east-1.amazonaws.com"
bucket = "my-bucket"

[profiles.my-sftp]
scheme = "sftp"
host   = "myserver.example.com"
port   = 22
user   = "alice"
```

Supported schemes: `s3`, `sftp`, `ssh`, `ftp`, `ftps`, `webdav`, `rclone`.

Credentials (passwords, API keys) are stored separately via the system keyring, not in this file.

## Named Sessions

Save and restore full pane layouts by name. Sessions include both panes, all tabs, and
panel positions. Stored as JSON entries in `~/.config/biome-fm/sessions/`.

Open the session picker via **File → Named Sessions**. Saved sessions survive restarts.

## Accessibility

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ui_font_size` | int | `0` | Override UI font size in pt. `0` = use system default. |
| `reduce_motion` | bool | `false` | Disable animations and transitions |
| `high_contrast` | bool | `false` | Enable high-contrast mode for improved readability |

## AI Settings

Configure AI providers via `~/.config/biome-fm/config.toml` or **Tools → AI Settings**.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ai_default_provider` | string | `"claude"` | Active provider: `"claude"`, `"openai"`, or `"ollama"` |
| `ai_claude_key` | string | `""` | Anthropic API key |
| `ai_claude_model` | string | `"claude-sonnet-4-20250514"` | Claude model ID |
| `ai_openai_key` | string | `""` | OpenAI API key |
| `ai_openai_model` | string | `"gpt-4o"` | OpenAI model ID |
| `ai_ollama_url` | string | `"http://localhost:11434"` | Ollama server URL |
| `ai_ollama_model` | string | `"llama3.2"` | Ollama model name |
| `ai_cli_claude_code_model` | string | `""` | Model override for Claude Code CLI integration |
| `ai_cli_codex_model` | string | `""` | Model override for Codex CLI integration |
| `ai_cli_opencode_model` | string | `""` | Model override for OpenCode CLI integration |

API keys are stored in plain text in the config file. Use the system keyring for production deployments if needed.
