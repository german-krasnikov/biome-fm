"""Read-only filesystem tools for MCP."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from biome_fm.models.vfs_router import VFSRouter

from . import _validate_path

_MAX_BYTES = 65536


def _list_directory(
    path: str, vfs: VFSRouter, allowed_roots: list[Path] | None = None
) -> list[dict[str, Any]]:
    p = _validate_path(path, allowed_roots)
    items = vfs.listdir(p)
    return [
        {
            "name": f.name,
            "path": str(f.path),
            "is_dir": f.is_dir,
            "size": f.size,
            "modified": f.modified,
        }
        for f in items
    ]


def _stat_item(
    path: str, vfs: VFSRouter, allowed_roots: list[Path] | None = None
) -> dict[str, Any]:
    p = _validate_path(path, allowed_roots)
    f = vfs.stat(p)
    return {
        "name": f.name,
        "path": str(f.path),
        "is_dir": f.is_dir,
        "size": f.size,
        "modified": f.modified,
        "permissions": f.permissions,
    }


def _read_file(
    path: str, max_bytes: int = _MAX_BYTES, allowed_roots: list[Path] | None = None
) -> dict[str, Any]:
    p = _validate_path(path, allowed_roots)
    size = p.stat().st_size
    raw = p.read_bytes()[:max_bytes]
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"content": "[binary file]", "truncated": False, "size": size}
    if "\x00" in content:
        return {"content": "[binary file]", "truncated": False, "size": size}
    return {"content": content, "truncated": size > max_bytes, "size": size}


def _search_files(
    root: str, pattern: str, recursive: bool = True, allowed_roots: list[Path] | None = None
) -> list[str]:
    p = _validate_path(root, allowed_roots)
    glob = p.rglob if recursive else p.glob
    return [str(f) for f in glob(pattern) if f.is_file()]


def register(mcp: Any, vfs: VFSRouter, allowed_roots: list[Path] | None = None) -> None:
    @mcp.tool()  # type: ignore[untyped-decorator]
    def list_directory(path: str) -> list[dict[str, Any]]:
        """List directory contents."""
        return _list_directory(path, vfs, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def stat_item(path: str) -> dict[str, Any]:
        """Get file/directory metadata."""
        return _stat_item(path, vfs, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def read_file(path: str, max_bytes: int = _MAX_BYTES) -> dict[str, Any]:
        """Read file content (text only, capped at max_bytes)."""
        return _read_file(path, max_bytes, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def search_files(root: str, pattern: str, recursive: bool = True) -> list[str]:
        """Search files by glob pattern."""
        return _search_files(root, pattern, recursive, allowed_roots)
