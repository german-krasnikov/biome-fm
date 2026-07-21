"""macOS Touch Bar support. No-op everywhere else and when pyobjc absent."""
from __future__ import annotations

from biome_fm.utils.platform import IS_MAC


def setup_touch_bar(window: object, actions: list[tuple[str, object]]) -> None:
    """Install Touch Bar with labelled buttons. No-op if unavailable."""
    if not IS_MAC:
        return
    try:
        from biome_fm.utils._touch_bar_impl import _setup  # type: ignore[import-not-found]
        _setup(window, actions)
    except (ImportError, Exception):
        return
