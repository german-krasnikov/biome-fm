"""Pluggy hook specifications for biome-fm plugins."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_fm.preview.provider import PreviewProvider

import pluggy

from biome_fm.plugins.types import ActionSpec, ColumnDef, ThemeTokens

hookspec = pluggy.HookspecMarker("biome_fm")
hookimpl = pluggy.HookimplMarker("biome_fm")


class BiomeFMSpec:
    @hookspec(historic=True)
    def register_commands(self, registry: object) -> None:
        """Called at startup — add CommandEntry items to the registry."""

    @hookspec
    def on_navigate(self, path: Path) -> None:
        """Called when a pane navigates to a new directory."""

    @hookspec
    def on_file_operation(self, op: str, src: Path, dst: Path | None) -> None:
        """Called after file ops. op: 'copy'|'move'|'delete'|'mkdir'."""

    @hookspec(firstresult=True)
    def provide_theme(self, name: str) -> ThemeTokens | None:
        """Return token dict for theme `name`, or None if not handled."""

    @hookspec(firstresult=True)
    def before_file_operation(self, op: str, src: Path, dst: Path | None) -> bool | None:
        """Return False to veto the operation. None = allow."""

    @hookspec
    def context_menu_actions(self, items: list[object], pane_id: str) -> list[ActionSpec]:
        """Return additional context menu actions."""

    @hookspec
    def extra_columns(self) -> list[ColumnDef]:
        """Return additional column definitions for the file listing."""

    @hookspec
    def extra_archive_extensions(self) -> list[str]:
        """Return list of archive extensions this plugin handles: ['rar', '7z']."""

    @hookspec(firstresult=True)
    def provide_vfs(self, path: str) -> object | None:
        """Return a VFS for the given path prefix, or None to pass through."""

    @hookspec
    def provide_preview_providers(self) -> list["PreviewProvider"]:
        """Return list of PreviewProvider instances this plugin contributes.

        THREADING: render() is called on a background ThreadPoolExecutor thread.
        Must not instantiate QWidget, QTextDocument, or any other Qt object.
        Return only plain PreviewResult dataclasses.
        """

    @hookspec(firstresult=True)
    def column_value(self, item: object, column_id: str) -> str | None:
        """Return display value for plugin column `column_id` for the given FileItem.
        Return None to leave cell empty. First non-None result wins."""
