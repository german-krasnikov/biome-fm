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
| `follow_system_theme` | bool | `true` | Track the OS light/dark theme automatically |
| `editor_cmd` | string | `""` | External editor command for `F4`. Empty = built-in editor |
| `show_git_status` | bool | `true` | Show git XY status column in file list |
| `auto_preview` | bool | `true` | Auto-open preview on cursor move |
| `hidden_columns` | list | `[]` | Column names to hide (`"Size"`, `"Modified"`, `"Ext"`, `"Git"`) |

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

## Column Visibility

Toggle columns via `Ctrl+Shift+Y` or by adding them to `hidden_columns`:

```toml
hidden_columns = ["Ext", "Git"]
```

Visibility is applied per-pane and persisted across sessions.

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
