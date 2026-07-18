"""Integration tests for PreviewPanel Ctrl+F in-pane search."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt

from biome_fm.preview.provider import ContentKind, PreviewResult
from biome_fm.views.preview_panel import PreviewPanel

_TEXT = "alpha\nbeta\ngamma\nalpha again"


def test_preview_ctrl_f_end_to_end(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data=_TEXT))
    qtbot.keyClick(panel, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert panel._find_bar.isVisible()
    panel._find_edit.setText("beta")
    assert panel._find_label.text() == "Found"


def test_find_wraps_around(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data=_TEXT))
    panel._show_find_bar()
    panel._find_edit.setText("alpha")
    panel._find_next()   # 2nd match ("alpha again")
    result = panel._find_next()  # wraps to 1st match
    assert result is True
    assert panel._find_label.text() == "Found"


def test_find_previous(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data=_TEXT))
    panel._show_find_bar()
    panel._find_edit.setText("alpha")
    panel._find_next()   # move to 2nd "alpha again"
    result = panel._find_prev()  # back to 1st "alpha"
    assert result is True
    assert panel._find_label.text() == "Found"


def test_find_label_clears_on_new_content(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data=_TEXT))
    panel._show_find_bar()
    panel._find_edit.setText("alpha")
    assert panel._find_label.text() == "Found"
    # Load new content — label must clear
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data="nothing here"))
    assert panel._find_label.text() == ""


def test_escape_closes_find_bar(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data=_TEXT))
    panel._show_find_bar()
    qtbot.keyClick(panel._find_edit, Qt.Key.Key_Escape)
    assert not panel._find_bar.isVisible()
