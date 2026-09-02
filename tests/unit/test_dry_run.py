"""TDD: F442 — Operation Preview / Dry-Run."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.commands.base import Command
from biome_fm.commands.copy_cmd import CopyCmd
from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.commands.move_cmd import MoveCmd

# --- pure-Python tests (no Qt) ---

class _NullCmd(Command):
    def execute(self) -> None: pass
    def undo(self) -> None: pass  # still abstract in base.py until task 03


def test_default_preview():
    cmd = _NullCmd()
    assert cmd.preview() == [cmd.description]


def test_preview_delete():
    paths = [Path("/a"), Path("/b")]
    cmd = DeleteCmd(paths, MagicMock())
    assert cmd.preview() == ["Delete /a", "Delete /b"]


def test_preview_move():
    src = Path("/src/a.txt")
    dest = Path("/dest")
    cmd = MoveCmd([src], dest, MagicMock())
    assert cmd.preview() == ["Move a.txt  →  /dest/a.txt"]


def test_preview_copy():
    src = Path("/src/a.txt")
    dest = Path("/dest")
    cmd = CopyCmd([src], dest, MagicMock())
    assert cmd.preview() == ["Copy a.txt  →  /dest/a.txt"]


# --- Qt dialog tests ---

def test_dry_run_dialog_shows_lines(qtbot):
    from biome_fm.views.dry_run_dialog import DryRunDialog

    cmd = MagicMock()
    cmd.description = "Test op"
    cmd.preview.return_value = ["line 1", "line 2", "line 3"]

    dlg = DryRunDialog(cmd)
    qtbot.addWidget(dlg)

    assert dlg._list.count() == 3
    assert dlg._list.item(0).text() == "line 1"


def test_dry_run_dialog_cancel_no_execute(qtbot):
    from biome_fm.views.dry_run_dialog import DryRunDialog

    cmd = MagicMock()
    cmd.description = "Test op"
    cmd.preview.return_value = ["do something"]

    dlg = DryRunDialog(cmd)
    qtbot.addWidget(dlg)
    dlg.reject()

    cmd.execute.assert_not_called()
