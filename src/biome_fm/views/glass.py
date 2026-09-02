"""Platform-native compositor blur via pyqt-liquidglass."""
from __future__ import annotations

import logging

_HAS_LIB = False
try:
    import pyqt_liquidglass as _glass
    _HAS_LIB = True
except ImportError:
    _glass = None  # type: ignore[assignment]

_warned = False


def is_available() -> bool:
    return _HAS_LIB


def configure_glass(window, enabled: bool) -> bool:
    """Tag window for glass when requested AND the lib is present. Returns the effective flag."""
    active = enabled and _HAS_LIB
    window._glass_cfg = active
    if active:
        from biome_fm.views.glass_style import mark_glass
        mark_glass(window, recursive=True)
    return active


def prepare_glass(window) -> bool:
    """Prepare window for glass (calls show() internally)."""
    global _warned
    if not _HAS_LIB:
        if not _warned:
            logging.getLogger(__name__).warning(
                "pyqt_liquidglass not installed; glass disabled (uv sync --all-extras)"
            )
            _warned = True
        return False
    try:
        _glass.prepare_window_for_glass(window)
        return True
    except Exception:
        return False


def enable_glass(window) -> bool:
    """Apply native blur effect. Window must be shown."""
    if not _HAS_LIB:
        return False
    try:
        _glass.apply_glass_to_window(window)
        return True
    except Exception:
        return False


def disable_glass(window) -> None:
    """Remove glass effect."""
    if _HAS_LIB:
        try:
            _glass.remove_glass_effect(window)
        except Exception:
            pass
