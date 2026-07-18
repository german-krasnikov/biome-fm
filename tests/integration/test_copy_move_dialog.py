"""Integration tests for CopyMoveDialog (F223)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton  # noqa: E402


class TestCopyMoveDialog:
    def test_dialog_has_combo_box(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog

        dlg = CopyMoveDialog("copy", [tmp_path / "f.txt"], tmp_path, [])
        qtbot.addWidget(dlg)
        combo = dlg.findChild(QComboBox)
        assert combo is not None
        assert combo.isEditable()

    def test_dialog_has_browse_button(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog

        dlg = CopyMoveDialog("copy", [tmp_path / "f.txt"], tmp_path, [])
        qtbot.addWidget(dlg)
        buttons = dlg.findChildren(QPushButton)
        labels = [b.text() for b in buttons]
        assert any("…" in t or "..." in t for t in labels)

    def test_dialog_history_populated(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog

        dest = tmp_path / "dest"
        history = [str(tmp_path / "prev1"), str(tmp_path / "prev2")]
        dlg = CopyMoveDialog("copy", [tmp_path / "f.txt"], dest, history)
        qtbot.addWidget(dlg)
        combo = dlg.findChild(QComboBox)
        assert combo is not None
        assert combo.count() >= 3  # dest + 2 history items


class TestVerifyCheckbox:
    """F211 — Copy with Verification UI Toggle."""

    def test_verify_checkbox_default_unchecked(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog

        dlg = CopyMoveDialog("copy", [tmp_path / "f.txt"], tmp_path, [])
        qtbot.addWidget(dlg)
        cb = dlg.findChild(QCheckBox)
        assert cb is not None
        assert not cb.isChecked()
        assert not dlg.verify_enabled

    def test_verify_property_reflects_checkbox(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog

        dlg = CopyMoveDialog("copy", [tmp_path / "f.txt"], tmp_path, [])
        qtbot.addWidget(dlg)
        cb = dlg.findChild(QCheckBox)
        assert cb is not None
        cb.setChecked(True)
        assert dlg.verify_enabled

    def test_verify_checkbox_hidden_for_move(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.copy_move_dialog import CopyMoveDialog

        dlg = CopyMoveDialog("move", [tmp_path / "f.txt"], tmp_path, [])
        qtbot.addWidget(dlg)
        # verify_enabled should always be False for move dialogs
        assert not dlg.verify_enabled
