"""F418 — Word Wrap Toggle in Preview."""
import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from biome_fm.views.preview_panel import PreviewPanel


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(app, qtbot):
    p = PreviewPanel()
    qtbot.addWidget(p)
    return p


def test_default_nowrap(panel):
    from PySide6.QtWidgets import QTextEdit
    assert panel._text_view.lineWrapMode() == QTextEdit.LineWrapMode.NoWrap


def test_wrap_button_exists(panel):
    btns = [b for b in panel.findChildren(QPushButton) if b.text() == "Wrap"]
    assert btns, "Wrap button not found"
    assert btns[0].isCheckable()


def test_toggle_on_sets_widgetwidth(panel):
    from PySide6.QtWidgets import QTextEdit
    panel._set_wrap(True)
    assert panel._text_view.lineWrapMode() == QTextEdit.LineWrapMode.WidgetWidth


def test_toggle_off_sets_nowrap(panel):
    from PySide6.QtWidgets import QTextEdit
    panel._set_wrap(True)
    panel._set_wrap(False)
    assert panel._text_view.lineWrapMode() == QTextEdit.LineWrapMode.NoWrap
