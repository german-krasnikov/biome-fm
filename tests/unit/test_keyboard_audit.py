"""F312 — Keyboard-Only Operation Audit."""
from __future__ import annotations

import inspect


def test_all_actions_have_shortcuts() -> None:
    """Alt+Return (properties) and Alt+B (bookmarks) must be wired in app.py."""
    import biome_fm.app

    source = inspect.getsource(biome_fm.app)
    assert "Alt+Return" in source, "Properties shortcut (Alt+Return) not wired in app.py"
    assert "Alt+B" in source, "Bookmark shortcut (Alt+B) not wired in app.py"
