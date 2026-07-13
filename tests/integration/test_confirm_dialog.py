"""Integration tests for ConfirmDialog — headless Qt."""
import os
import pytest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.views.confirm_dialog import ConfirmDialog  # noqa: E402


@pytest.fixture
def sources():
    return [Path(f"/tmp/file{i}.txt") for i in range(3)]


def test_dialog_title_copy(qtbot, sources):
    dlg = ConfirmDialog("copy", sources, dest=Path("/dst"))
    qtbot.addWidget(dlg)
    assert "Copy" in dlg.windowTitle()


def test_dialog_title_delete(qtbot, sources):
    dlg = ConfirmDialog("delete", sources)
    qtbot.addWidget(dlg)
    assert "Delete" in dlg.windowTitle()


def test_dialog_shows_dest_for_copy(qtbot, sources):
    dst = Path("/Users/foo/Backup")
    dlg = ConfirmDialog("copy", sources, dest=dst)
    qtbot.addWidget(dlg)
    dest_lbl = dlg.findChild(object, "confirm_dest")
    assert dest_lbl is not None
    assert str(dst) in dest_lbl.text()


def test_dialog_no_dest_for_delete(qtbot, sources):
    dlg = ConfirmDialog("delete", sources)
    qtbot.addWidget(dlg)
    dest_lbl = dlg.findChild(object, "confirm_dest")
    assert dest_lbl is None


def test_dialog_truncates_long_list(qtbot):
    srcs = [Path(f"/tmp/f{i}.txt") for i in range(10)]
    dlg = ConfirmDialog("delete", srcs)
    qtbot.addWidget(dlg)
    # find overflow label
    from PySide6.QtWidgets import QLabel
    labels = dlg.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]
    overflow = [t for t in texts if "more" in t]
    assert len(overflow) == 1
    assert "5 more" in overflow[0]


def test_danger_button_for_delete(qtbot, sources):
    dlg = ConfirmDialog("delete", sources)
    qtbot.addWidget(dlg)
    from PySide6.QtWidgets import QPushButton
    btns = dlg.findChildren(QPushButton)
    danger_btns = [b for b in btns if b.objectName() == "danger"]
    assert len(danger_btns) == 1
