"""Platform-native compositor blur via pyqt-liquidglass."""
from __future__ import annotations

_HAS_LIB = False
try:
    import pyqt_liquidglass as _glass
    _HAS_LIB = True
except ImportError:
    _glass = None  # type: ignore[assignment]


def prepare_glass(window) -> bool:
    """Prepare window for glass (calls show() internally)."""
    if not _HAS_LIB:
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
