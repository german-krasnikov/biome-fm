"""Atomic read-patch-write for AI client configs (JSON and TOML)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .clients import SERVER_NAME, ClientInfo


def merge_config(client: ClientInfo, entry: dict[str, Any]) -> None:
    """Patch client JSON config: set data[root_key][SERVER_NAME] = entry, atomic write."""
    path = client.config_path
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    section = data.setdefault(client.root_key, {})
    section[SERVER_NAME] = client.entry_transformer(entry) if client.entry_transformer else entry
    _atomic_write_json(path, data)


def remove_entry(client: ClientInfo) -> bool:
    """Remove SERVER_NAME from client JSON config. Returns True if found and removed."""
    path = client.config_path
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    section = data.get(client.root_key, {})
    if SERVER_NAME not in section:
        return False
    del section[SERVER_NAME]
    _atomic_write_json(path, data)
    return True


def merge_toml_config(path: Path, entry: dict[str, Any]) -> None:
    """Write/update [mcp_servers."biome-fm"] section in a TOML file."""
    header = f'[mcp_servers."{SERVER_NAME}"]'
    lines = [header]
    for k, v in entry.items():
        lines.append(f"{k} = {_toml_value(v)}")
    section = "\n".join(lines) + "\n"

    if path.exists():
        content = _remove_toml_section(path.read_text(encoding="utf-8"))
        content = content.rstrip("\n") + "\n\n" + section
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = section

    _atomic_write(path, content)


def remove_toml_entry(path: Path) -> bool:
    """Remove [mcp_servers."biome-fm"] section. Returns True if found."""
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    header = f'[mcp_servers."{SERVER_NAME}"]'
    if header not in content:
        return False
    _atomic_write(path, _remove_toml_section(content))
    return True


# --- helpers ---

def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    _atomic_write(path, json.dumps(data, indent=2))


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _toml_value(v: object) -> str:
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list):
        items = '"' + '", "'.join(str(x).replace("\\", "\\\\").replace('"', '\\"') for x in v) + '"'
        return f"[{items}]" if v else "[]"
    return str(v).lower() if isinstance(v, bool) else str(v)


def _remove_toml_section(content: str) -> str:
    """Strip [mcp_servers."biome-fm"] and its key lines from TOML text."""
    header = f'[mcp_servers."{SERVER_NAME}"]'
    lines = content.split("\n")
    result: list[str] = []
    skip = False
    for line in lines:
        if line.strip() == header:
            skip = True
            continue
        if skip and line.strip().startswith("["):
            skip = False
        if not skip:
            result.append(line)
    return "\n".join(result)
