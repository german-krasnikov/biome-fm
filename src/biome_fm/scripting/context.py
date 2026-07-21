"""Scripting namespace injected into exec'd code. Qt-free."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.commands.registry import CommandRegistry


class BiomeContext:
    """Public API available as `biome` inside user scripts."""

    def __init__(self, active_pane: "PanePresenter", registry: "CommandRegistry") -> None:
        self._pane = active_pane
        self._registry = registry

    def navigate(self, path: str | Path) -> None:
        self._pane.navigate(Path(path))

    def execute(self, command_id: str) -> None:
        self._registry.execute(command_id)

    @property
    def current_path(self) -> Path:
        return self._pane.current_path

    @property
    def selected(self) -> list[Path]:
        return [item.path for item in self._pane.marked_items()]
