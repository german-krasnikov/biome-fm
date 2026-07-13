"""MCP server factory for biome-fm."""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from biome_fm.commands.base import CommandHistory
from biome_fm.mcp.tools import fs_read, fs_write
from biome_fm.models.vfs_router import VFSRouter


def create_server(allowed_roots: list[Path] | None = None) -> FastMCP:
    vfs = VFSRouter()
    history = CommandHistory()
    mcp = FastMCP("biome-fm")
    fs_read.register(mcp, vfs, allowed_roots)
    fs_write.register(mcp, vfs, history, allowed_roots)
    return mcp
