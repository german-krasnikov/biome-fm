"""AI client registry — known clients and their config paths."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SERVER_NAME = "biome-fm"


@dataclass
class ClientInfo:
    name: str
    config_path: Path
    scope: str  # "user" | "project"
    root_key: str  # "mcpServers" | "servers" | "mcp"
    stdout_only: bool = False
    is_toml: bool = False
    entry_transformer: Callable[[dict[str, object]], dict[str, object]] | None = None
    binary: str | None = None  # executable name for shutil.which detection


def _vscode_transformer(entry: dict[str, object]) -> dict[str, object]:
    return {**entry, "type": "stdio"}


def _opencode_transformer(entry: dict[str, object]) -> dict[str, object]:
    cmd = str(entry.get("command", ""))
    args = list(entry.get("args", []))  # type: ignore[call-overload]
    return {"type": "local", "command": [cmd, *args]}


def _build_registry() -> dict[str, ClientInfo]:
    h = Path.home()
    reg: dict[str, ClientInfo] = {}

    reg["claude-code"] = ClientInfo(
        name="Claude Code",
        config_path=h / ".claude.json",
        scope="user",
        root_key="mcpServers",
        binary="claude",
    )

    if sys.platform == "darwin":
        _claude_desktop = h / "Library/Application Support/Claude/claude_desktop_config.json"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA", str(h))
        _claude_desktop = Path(appdata) / "Claude/claude_desktop_config.json"
    else:
        _claude_desktop = h / ".config/Claude/claude_desktop_config.json"

    reg["claude-desktop"] = ClientInfo(
        name="Claude Desktop",
        config_path=_claude_desktop,
        scope="user",
        root_key="mcpServers",
        binary="claude" if sys.platform != "darwin" else None,
    )

    reg["cursor"] = ClientInfo(
        name="Cursor",
        config_path=h / ".cursor/mcp.json",
        scope="user",
        root_key="mcpServers",
        binary="cursor",
    )

    reg["windsurf"] = ClientInfo(
        name="Windsurf",
        config_path=h / ".codeium/windsurf/mcp_config.json",
        scope="user",
        root_key="mcpServers",
        binary="windsurf",
    )

    if sys.platform == "darwin":
        _vscode = h / "Library/Application Support/Code/User/settings.json"
    elif sys.platform == "win32":
        _vscode = Path(os.environ.get("APPDATA", str(h))) / "Code/User/settings.json"
    else:
        _vscode = h / ".config/Code/User/settings.json"

    reg["vscode"] = ClientInfo(
        name="VS Code",
        config_path=_vscode,
        scope="user",
        root_key="servers",
        entry_transformer=_vscode_transformer,
        binary="code",
    )

    reg["opencode"] = ClientInfo(
        name="OpenCode",
        config_path=h / ".config/opencode/config.json",
        scope="user",
        root_key="mcp",
        entry_transformer=_opencode_transformer,
        binary="opencode",
    )

    reg["codex"] = ClientInfo(
        name="Codex",
        config_path=h / ".codex/config.toml",
        scope="user",
        root_key="mcp_servers",
        is_toml=True,
        binary="codex",
    )

    reg["kimi"] = ClientInfo(
        name="Kimi Code",
        config_path=h / ".kimi-code/mcp.json",
        scope="user",
        root_key="mcpServers",
        binary="kimi",
    )

    return reg


CLIENT_REGISTRY: dict[str, ClientInfo] = _build_registry()


def detect_installed() -> list[str]:
    """Return keys for clients that appear to be installed.

    A client is considered installed when its config already exists OR
    when its binary can be found on PATH (shutil.which).
    """
    result = []
    for key, info in CLIENT_REGISTRY.items():
        if info.config_path.exists() or (info.binary and shutil.which(info.binary)):
            result.append(key)
    return result
