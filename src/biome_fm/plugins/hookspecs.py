"""Pluggy hook specifications for biome-fm plugins."""
from __future__ import annotations

from pathlib import Path

import pluggy

hookspec = pluggy.HookspecMarker("biome_fm")
hookimpl = pluggy.HookimplMarker("biome_fm")


class BiomeFMSpec:
    @hookspec
    def register_commands(self, registry: object) -> None:
        """Called at startup — add CommandEntry items to the registry."""

    @hookspec
    def on_navigate(self, path: Path) -> None:
        """Called when a pane navigates to a new directory."""

    @hookspec
    def on_file_operation(self, op: str, src: Path, dst: Path | None) -> None:
        """Called after file ops. op: 'copy'|'move'|'delete'|'mkdir'."""
