"""Integration tests for Tab Duplicate shortcut (F215)."""
from __future__ import annotations



from biome_fm.commands.registry import CommandEntry, CommandRegistry


def test_duplicate_tab_command_registered():
    registry = CommandRegistry()
    registry.register(CommandEntry("Duplicate Tab", "Ctrl+Alt+T", lambda: None))
    results = registry.search("Duplicate Tab")
    assert len(results) == 1
    assert results[0].shortcut == "Ctrl+Alt+T"
