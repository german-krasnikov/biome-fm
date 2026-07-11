"""PluginManager — loads plugins via entry_points, dispatches hooks."""
from __future__ import annotations

import importlib.metadata
from pathlib import Path

import pluggy

from biome_fm.plugins.hookspecs import BiomeFMSpec


class PluginManager:
    def __init__(self) -> None:
        self._pm = pluggy.PluginManager("biome_fm")
        self._pm.add_hookspecs(BiomeFMSpec)

    def load_entry_points(self) -> None:
        """Discover and load plugins from 'biome_fm.plugins' entry_points group."""
        for ep in importlib.metadata.entry_points(group="biome_fm.plugins"):
            try:
                plugin_cls = ep.load()
                self._pm.register(plugin_cls())
            except Exception:
                pass  # ponytail: silent skip, add logging later

    def register_plugin(self, plugin: object) -> None:
        """Register a plugin object directly (for testing / built-in plugins)."""
        self._pm.register(plugin)

    def register_commands(self, registry: object) -> None:
        self._pm.hook.register_commands(registry=registry)

    def on_navigate(self, path: Path) -> None:
        self._pm.hook.on_navigate(path=path)

    def on_file_operation(self, op: str, src: Path, dst: Path | None = None) -> None:
        self._pm.hook.on_file_operation(op=op, src=src, dst=dst)
