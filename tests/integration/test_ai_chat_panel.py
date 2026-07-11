"""Integration tests for AIChatPanel."""
import pytest

from biome_fm.views.ai_chat_panel import AIChatPanel


@pytest.fixture
def panel(qtbot):
    w = AIChatPanel()
    qtbot.addWidget(w)
    w.show()
    return w


def test_message_submitted_on_return(panel, qtbot):
    received = []
    panel.message_submitted.connect(received.append)
    panel._input.setText("hello")
    panel._input.returnPressed.emit()
    assert received == ["hello"]
    assert panel._input.text() == ""


def test_message_submitted_on_button(panel, qtbot):
    received = []
    panel.message_submitted.connect(received.append)
    panel._input.setText("world")
    panel._send_btn.click()
    assert received == ["world"]


def test_empty_input_not_submitted(panel, qtbot):
    received = []
    panel.message_submitted.connect(received.append)
    panel._input.setText("   ")
    panel._input.returnPressed.emit()
    assert received == []


def test_set_busy_disables_input(panel):
    panel.set_busy(True)
    assert not panel._input.isEnabled()
    assert not panel._send_btn.isEnabled()
    panel.set_busy(False)
    assert panel._input.isEnabled()
    assert panel._send_btn.isEnabled()


def test_append_message_adds_text(panel):
    panel.append_message("user", "test msg")
    html = panel._log.toHtml()
    assert "You:" in html
    assert "test msg" in html
