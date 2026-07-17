"""Integration tests for ConflictDialog."""
import pytest

from biome_fm.models.conflict_resolver import ConflictAction
from biome_fm.views.conflict_dialog import ConflictDialog
from biome_fm.qt import QLabel, QPushButton


@pytest.fixture()
def file_pair(tmp_path):
    src = tmp_path / "report.txt"
    src.write_text("new version")
    dst = tmp_path / "dst" / "report.txt"
    (tmp_path / "dst").mkdir()
    dst.write_text("old version")
    return src, dst


def test_dialog_shows_filenames(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    dlg.show()
    all_text = " ".join(w.text() for w in dlg.findChildren(QLabel))
    assert "report.txt" in all_text


def test_overwrite_button_action(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    btn = next(b for b in dlg.findChildren(QPushButton) if "Overwrite" in b.text() and "All" not in b.text())
    btn.click()
    assert dlg.action == ConflictAction.OVERWRITE


def test_skip_button_action(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Skip")
    btn.click()
    assert dlg.action == ConflictAction.SKIP


def test_skip_all_button_action(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Skip All")
    btn.click()
    assert dlg.action == ConflictAction.SKIP_ALL


def test_overwrite_all_button_action(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Overwrite All")
    btn.click()
    assert dlg.action == ConflictAction.OVERWRITE_ALL


def test_rename_button_action(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Rename")
    btn.click()
    assert dlg.action == ConflictAction.RENAME


def test_cancel_button_action(qtbot, file_pair):
    src, dst = file_pair
    dlg = ConflictDialog(src, dst)
    qtbot.addWidget(dlg)
    btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Cancel")
    btn.click()
    assert dlg.action == ConflictAction.CANCEL
