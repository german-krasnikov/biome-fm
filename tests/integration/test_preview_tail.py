"""F416 — Lister Auto-Scroll / Tail Mode — integration tests."""
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


def test_tail_button_exists(panel):
    btns = [b for b in panel.findChildren(QPushButton) if b.text() == "Tail"]
    assert btns, "Tail button not found"
    assert btns[0].isCheckable()


def test_tail_toggled_signal_on(panel, qtbot):
    btn = next(b for b in panel.findChildren(QPushButton) if b.text() == "Tail")
    btn.setChecked(False)
    with qtbot.waitSignal(panel.tail_toggled, timeout=1000) as blocker:
        btn.click()
    assert blocker.args == [True]


def test_tail_toggled_signal_off(panel, qtbot):
    btn = next(b for b in panel.findChildren(QPushButton) if b.text() == "Tail")
    btn.setChecked(True)
    with qtbot.waitSignal(panel.tail_toggled, timeout=1000) as blocker:
        btn.click()
    assert blocker.args == [False]


def test_scroll_to_bottom(panel, qtbot):
    panel.resize(400, 300)
    panel.show()
    qtbot.waitExposed(panel)
    panel._text_view.setPlainText("\n".join(str(i) for i in range(500)))
    panel._stack.setCurrentWidget(panel._text_view)
    panel._text_view.verticalScrollBar().setValue(0)
    panel.scroll_to_bottom()
    sb = panel._text_view.verticalScrollBar()
    assert sb.maximum() > 0, "viewport must be non-zero for this test to be meaningful"
    assert sb.value() == sb.maximum()
