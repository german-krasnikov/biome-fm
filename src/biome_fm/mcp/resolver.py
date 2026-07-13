"""Resolve the biome-fm MCP server command."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any


def find_server_command() -> list[str]:
    """Priority: uvx > venv bin > sys.executable -m."""
    uvx = shutil.which("uvx")
    if uvx:
        return [uvx, "biome-fm-mcp"]

    venv_bin = Path(sys.executable).parent / "biome-fm-mcp"
    if venv_bin.exists():
        return [str(venv_bin)]

    return [sys.executable, "-m", "biome_fm.mcp._entry"]


def build_server_entry(cmd: list[str] | None = None) -> dict[str, Any]:
    """Return canonical MCP server entry: {"command": ..., "args": [...]}."""
    if cmd is None:
        cmd = find_server_command()
    return {"command": cmd[0], "args": cmd[1:]}
