# CLI Installer

biome-fm ships with subcommands that register it in AI client configurations
(Claude Code, Cursor, VS Code, Windsurf, OpenCode, Codex, Kimi, Claude Desktop).

These subcommands run before Qt loads, so they work headlessly in CI or over SSH.

## Commands

```bash
biome-fm configure                    # auto-detect installed clients and register biome-fm in each
biome-fm configure --client=cursor    # target a specific client only
biome-fm doctor                       # verify registration is present in all found clients
biome-fm version                      # print biome-fm version and exit
biome-fm uninstall                    # remove biome-fm entry from all found client configs
biome-fm uninstall --client=cursor    # target a specific client only
```

## Supported Clients

| Client | Config format |
|--------|--------------|
| claude-code | JSON |
| claude-desktop | JSON |
| cursor | JSON |
| windsurf | JSON |
| vscode | JSON |
| opencode | TOML |
| codex | JSON |
| kimi | JSON |

## How It Works

`configure` calls `cli/resolver.py` to find the best biome-fm command:

1. `uvx run biome-fm` (preferred — isolated environment)
2. `.venv/bin/biome-fm` (project venv)
3. `python -m biome_fm` (fallback)

The resolved command is written atomically into each client's config under the `biome-fm` key.
JSON clients use a tmp-file + `os.replace` strategy. TOML clients use a section merge.
