"""Write filesystem tools for MCP — mutations via Command pattern."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from biome_fm.commands.base import CommandHistory
from biome_fm.commands.copy_cmd import CopyCmd
from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.commands.mkdir_cmd import MkdirCmd
from biome_fm.commands.move_cmd import MoveCmd
from biome_fm.commands.rename_cmd import RenameCmd
from biome_fm.models.vfs_router import VFSRouter

from . import _validate_path


def _copy_files(
    sources: list[str], destination: str, vfs: VFSRouter, history: CommandHistory,
    allowed_roots: list[Path] | None = None,
) -> dict[str, Any]:
    srcs = [_validate_path(s, allowed_roots) for s in sources]
    dst = _validate_path(destination, allowed_roots)
    cmd = CopyCmd(srcs, dst, vfs)
    history.execute(cmd)
    return {"copied": len(srcs), "destination": destination}


def _move_files(
    sources: list[str], destination: str, vfs: VFSRouter, history: CommandHistory,
    allowed_roots: list[Path] | None = None,
) -> dict[str, Any]:
    srcs = [_validate_path(s, allowed_roots) for s in sources]
    dst = _validate_path(destination, allowed_roots)
    cmd = MoveCmd(srcs, dst, vfs)
    history.execute(cmd)
    return {"moved": len(srcs), "destination": destination}


def _delete_files(
    paths: list[str], vfs: VFSRouter, history: CommandHistory,
    allowed_roots: list[Path] | None = None,
) -> dict[str, Any]:
    ps = [_validate_path(p, allowed_roots) for p in paths]
    cmd = DeleteCmd(ps, vfs)
    history.execute(cmd)
    return {"deleted": len(ps)}


def _mkdir(
    path: str, vfs: VFSRouter, history: CommandHistory,
    allowed_roots: list[Path] | None = None,
) -> dict[str, Any]:
    p = _validate_path(path, allowed_roots)
    cmd = MkdirCmd(p, vfs)
    history.execute(cmd)
    return {"created": path}


def _rename_file(
    path: str, new_name: str, vfs: VFSRouter, history: CommandHistory,
    allowed_roots: list[Path] | None = None,
) -> dict[str, Any]:
    src = _validate_path(path, allowed_roots)
    cmd = RenameCmd(src, new_name, vfs)
    history.execute(cmd)
    return {"old": path, "new": str(src.parent / new_name)}


def _undo_last(history: CommandHistory) -> dict[str, Any]:
    if not history.can_undo:
        return {"undone": False, "reason": "nothing to undo"}
    history.undo()
    return {"undone": True}


def register(
    mcp: Any, vfs: VFSRouter, history: CommandHistory, allowed_roots: list[Path] | None = None
) -> None:
    @mcp.tool()  # type: ignore[untyped-decorator]
    def copy_files(sources: list[str], destination: str) -> dict[str, Any]:
        """Copy files to destination directory."""
        return _copy_files(sources, destination, vfs, history, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def move_files(sources: list[str], destination: str) -> dict[str, Any]:
        """Move files to destination directory."""
        return _move_files(sources, destination, vfs, history, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def delete_files(paths: list[str]) -> dict[str, Any]:
        """Delete files (non-undoable)."""
        return _delete_files(paths, vfs, history, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def make_directory(path: str) -> dict[str, Any]:
        """Create a directory."""
        return _mkdir(path, vfs, history, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def rename_file(path: str, new_name: str) -> dict[str, Any]:
        """Rename a file or directory."""
        return _rename_file(path, new_name, vfs, history, allowed_roots)

    @mcp.tool()  # type: ignore[untyped-decorator]
    def undo_last() -> dict[str, Any]:
        """Undo the last file operation."""
        return _undo_last(history)
