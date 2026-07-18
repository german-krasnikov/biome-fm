"""Unit tests for PreviewPanel find bar — requires Qt (offscreen)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt

from biome_fm.preview.provider import ContentKind, PreviewResult
from biome_fm.views.preview_panel import PreviewPanel


def test_find_bar_hidden_by_default(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    assert not panel._find_bar.isVisible()


def test_ctrl_f_shows_find_bar(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.keyClick(panel, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert panel._find_bar.isVisible()


def test_type_query_finds_text(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data="Hello World\nSecond line"))
    panel._show_find_bar()
    panel._find_edit.setText("Hello")
    assert panel._find_label.text() == "Found"


def test_escape_hides_find_bar(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel._show_find_bar()
    assert panel._find_bar.isVisible()
    qtbot.keyClick(panel._find_edit, Qt.Key.Key_Escape)
    assert not panel._find_bar.isVisible()


def test_f3_finds_next_match_via_keyboard(qtbot):
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.show_result(PreviewResult(kind=ContentKind.TEXT, data="foo bar foo baz"))
    panel._show_find_bar()
    panel._find_edit.setText("foo")
    panel._find_next()
    assert panel._find_label.text() == "Found"
