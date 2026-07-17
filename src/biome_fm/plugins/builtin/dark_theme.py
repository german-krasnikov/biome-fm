"""Built-in dark theme plugin."""
from __future__ import annotations

from biome_fm.plugins.hookspecs import hookimpl
from biome_fm.plugins.types import _DARK_FALLBACK, ThemeTokens


class BuiltinDarkTheme:
    BIOME_FM_API_VERSION = (1, 0)

    @hookimpl
    def provide_theme(self, name: str) -> ThemeTokens | None:
        if name == "dark":
            return dict(_DARK_FALLBACK)
        return None
