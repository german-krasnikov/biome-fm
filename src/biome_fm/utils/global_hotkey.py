"""F321 — Global hotkey registration via optional pynput dependency."""
from __future__ import annotations

from collections.abc import Callable


def register_global_hotkey(key_combo: str, callback: Callable) -> object | None:
    """Register a global hotkey. Returns listener handle or None if pynput unavailable."""
    try:
        from pynput import keyboard
    except (ImportError, TypeError):
        return None
    try:
        listener = keyboard.GlobalHotKeys({key_combo: callback})
        listener.start()
        return listener
    except Exception:
        return None
