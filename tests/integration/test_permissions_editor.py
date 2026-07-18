"""Integration tests for PermissionsEditorDialog (F210)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QCheckBox  # noqa: E402


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
class TestPermissionsEditorDialog:
    def test_dialog_has_checkboxes(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.permissions_editor_dialog import PermissionsEditorDialog

        f = tmp_path / "f.txt"
        f.write_bytes(b"x")
        dlg = PermissionsEditorDialog([f])
        qtbot.addWidget(dlg)
        checkboxes = dlg.findChildren(QCheckBox)
        # 9 permission bits + 1 recursive = at least 9
        assert len(checkboxes) >= 9

    def test_octal_input(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.permissions_editor_dialog import (
            PermissionsEditorDialog,
            _mode_from_checkboxes,
        )

        f = tmp_path / "f.txt"
        f.write_bytes(b"x")
        dlg = PermissionsEditorDialog([f])
        qtbot.addWidget(dlg)
        # Manually check owner-r, owner-w, owner-x, group-r, others-r (0o755)
        checks = dlg._checks
        assert len(checks) == 9
        # set: owner rwx=0o700, group r=0o040, group x=0o010, others r=0o004, others x=0o001
        # i.e., 0o755: bits 0o400 0o200 0o100 0o040 0o010 0o004 0o001
        for i, should_check in enumerate([True, True, True, True, False, True, True, False, True]):
            checks[i].setChecked(should_check)
        assert dlg.mode == 0o755
