"""Unit tests for CopyMoveDialog (F223)."""
from __future__ import annotations

from pathlib import Path


os_environ_patch = None  # QApplication provided by conftest / pytest-qt


def test_heading_copy() -> None:
    from biome_fm.views.copy_move_dialog import _heading

    assert _heading("copy", 3) == "Copy 3 items to:"


def test_heading_move_singular() -> None:
    from biome_fm.views.copy_move_dialog import _heading

    assert _heading("move", 1) == "Move 1 item to:"


def test_dialog_copy_title(qtbot, tmp_path: Path) -> None:
    from biome_fm.views.copy_move_dialog import CopyMoveDialog

    dlg = CopyMoveDialog("copy", [tmp_path / "a.txt"], tmp_path, [])
    qtbot.addWidget(dlg)
    assert "Copy" in dlg.windowTitle()


def test_dialog_move_title(qtbot, tmp_path: Path) -> None:
    from biome_fm.views.copy_move_dialog import CopyMoveDialog

    dlg = CopyMoveDialog("move", [tmp_path / "a.txt"], tmp_path, [])
    qtbot.addWidget(dlg)
    assert "Move" in dlg.windowTitle()


def test_dialog_default_dest(qtbot, tmp_path: Path) -> None:
    from biome_fm.views.copy_move_dialog import CopyMoveDialog

    dest = tmp_path / "dest"
    dlg = CopyMoveDialog("copy", [tmp_path / "a.txt"], dest, [])
    qtbot.addWidget(dlg)
    assert dlg.destination == dest


def test_dialog_file_list_preview(qtbot, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QLabel

    from biome_fm.views.copy_move_dialog import CopyMoveDialog

    srcs = [tmp_path / "a.txt", tmp_path / "b.txt"]
    dlg = CopyMoveDialog("copy", srcs, tmp_path, [])
    qtbot.addWidget(dlg)
    # heading label should mention the file count
    labels = dlg.findChildren(QLabel)
    texts = " ".join(lbl.text() for lbl in labels)
    assert "2" in texts


def test_verify_checkbox_default_false(qtbot, tmp_path: Path) -> None:
    from biome_fm.views.copy_move_dialog import CopyMoveDialog

    dlg = CopyMoveDialog("copy", [tmp_path / "a.txt"], tmp_path, [])
    qtbot.addWidget(dlg)
    assert dlg.verify_enabled is False


def test_verify_checkbox_not_shown_for_move(qtbot, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QCheckBox

    from biome_fm.views.copy_move_dialog import CopyMoveDialog

    dlg = CopyMoveDialog("move", [tmp_path / "a.txt"], tmp_path, [])
    qtbot.addWidget(dlg)
    boxes = dlg.findChildren(QCheckBox)
    assert not any("Verify" in b.text() for b in boxes)
