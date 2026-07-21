"""Unit tests for F455 — Custom Toolbar Builder."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.config import Config


# ── pure Python ──────────────────────────────────────────────────────────────

def _reg() -> CommandRegistry:
    reg = CommandRegistry()
    reg.register(CommandEntry("Copy", "Ctrl+C", lambda: None))
    reg.register(CommandEntry("Move", "Ctrl+M", lambda: None))
    return reg


def test_get_entry_found():
    reg = _reg()
    e = reg.get_entry("Copy")
    assert e.name == "Copy"


def test_get_entry_missing():
    reg = _reg()
    with pytest.raises(KeyError):
        reg.get_entry("bogus")


def test_config_toolbar_defaults():
    cfg = Config()
    assert cfg.toolbar_actions == []
    assert cfg.toolbar_visible is False


# ── Qt ───────────────────────────────────────────────────────────────────────

def test_load_actions_two(qtbot):
    from biome_fm.views.toolbar import CustomToolBar
    reg = _reg()
    tb = CustomToolBar(reg)
    qtbot.addWidget(tb)
    tb.load_actions(["Copy", "Move"])
    assert len(tb.actions()) == 2


def test_load_actions_skips_unknown(qtbot):
    from biome_fm.views.toolbar import CustomToolBar
    reg = _reg()
    tb = CustomToolBar(reg)
    qtbot.addWidget(tb)
    tb.load_actions(["Copy", "UNKNOWN"])
    assert len(tb.actions()) == 1


def test_load_actions_empty(qtbot):
    from biome_fm.views.toolbar import CustomToolBar
    reg = _reg()
    tb = CustomToolBar(reg)
    qtbot.addWidget(tb)
    tb.load_actions([])
    assert len(tb.actions()) == 0


def test_dialog_right_list_populated(qtbot):
    from biome_fm.views.toolbar_builder_dialog import ToolbarBuilderDialog
    reg = _reg()
    dlg = ToolbarBuilderDialog(reg, current=["Copy"])
    qtbot.addWidget(dlg)
    assert dlg._right.count() == 1
