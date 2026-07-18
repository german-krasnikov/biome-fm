"""Integration test: SyncDialog has 'Include subdirectories' checkbox."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from pathlib import Path

from biome_fm.views.sync_dialog import SyncDialog


@pytest.fixture
def dialog(qtbot):
    dlg = SyncDialog([], Path("/left"), Path("/right"))
    qtbot.addWidget(dlg)
    return dlg


def test_sync_dialog_subdirs_checkbox(dialog) -> None:
    assert hasattr(dialog, "_subdirs_chk"), "Missing _subdirs_chk checkbox"


def test_sync_dialog_subdirs_checkbox_is_unchecked_by_default(dialog) -> None:
    assert not dialog._subdirs_chk.isChecked()
