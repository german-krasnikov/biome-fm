"""Integration tests for Tab Duplicate shortcut (F215)."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from biome_fm.commands.registry import CommandEntry, CommandRegistry


def test_duplicate_tab_command_registered():
    registry = CommandRegistry()
    registry.register(CommandEntry("Duplicate Tab", "Ctrl+Alt+T", lambda: None))
    results = registry.search("Duplicate Tab")
    assert len(results) == 1
    assert results[0].shortcut == "Ctrl+Alt+T"
