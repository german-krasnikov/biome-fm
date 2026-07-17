"""ThemeRegistry — resolves theme tokens via plugin hook with fallback."""
from __future__ import annotations

import pluggy

from biome_fm.plugins.types import _DARK_FALLBACK


class ThemeRegistry:
    def __init__(self, pm: pluggy.PluginManager) -> None:
        self._pm = pm

    def resolve(self, name: str) -> dict:
        """Return tokens for `name`, merging plugin result over _DARK_FALLBACK."""
        tokens = self._pm.hook.provide_theme(name=name)
        # firstresult → single dict or None; empty list → None path for no plugins
        return {**_DARK_FALLBACK, **(tokens or {})}  # type: ignore[misc]
