"""Integration tests for AIChatPanel — Qt required."""
from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QUrl


from biome_fm.views.ai_chat_panel import AIChatPanel


@pytest.fixture
def panel(qtbot):
    p = AIChatPanel()
    qtbot.addWidget(p)
    p.show()
    return p


def test_panel_creates_without_error(panel):
    assert panel is not None


def test_append_message_shows_in_log(panel):
    panel.append_message("user", "Hello")
    assert "Hello" in panel._log.toPlainText()


def test_append_message_assistant(panel):
    panel.append_message("assistant", "Hi there")
    assert "Hi there" in panel._log.toPlainText()


def test_set_busy_disables_input(panel):
    panel.set_busy(True)
    assert not panel._send_btn.isEnabled()
    assert not panel._input.isEnabled()
    assert panel._cancel_btn.isVisible()


def test_set_busy_false_enables(panel):
    panel.set_busy(True)
    panel.set_busy(False)
    assert panel._send_btn.isEnabled()
    assert panel._input.isEnabled()
    assert not panel._cancel_btn.isVisible()


def test_send_emits_signal(panel, qtbot):
    panel._input.setPlainText("test message")
    with qtbot.waitSignal(panel.message_submitted):
        panel._on_send()
    assert panel._input.toPlainText() == ""


def test_send_empty_does_nothing(panel):
    panel._input.setPlainText("  ")
    emitted = []
    panel.message_submitted.connect(lambda t: emitted.append(t))
    panel._on_send()
    assert emitted == []


def test_model_combo_populated(panel):
    panel.set_provider_list(["claude", "openai"], "claude", ["sonnet", "opus"], "sonnet")
    assert panel._provider_combo.count() == 2
    assert panel._model_combo.count() == 2
    assert panel._model_combo.currentText() == "sonnet"


def test_provider_changed_signal(panel, qtbot):
    panel.set_provider_list(["claude", "openai"], "claude", ["m1"], "m1")
    with qtbot.waitSignal(panel.provider_changed):
        panel._provider_combo.setCurrentText("openai")


def test_context_bar_hidden_initially(panel):
    assert not panel._context_bar.isVisible()


def test_add_chip_shows_context_bar(panel):
    panel.add_attachment_chip("file.txt")
    assert panel._context_bar.isVisible()


def test_clear_chips_hides_context_bar(panel):
    panel.add_attachment_chip("file.txt")
    panel.clear_attachment_chips()
    assert not panel._context_bar.isVisible()


def test_streaming_tokens(panel):
    panel.append_token("Hello")
    panel.append_token(" world")
    panel.finalize_stream()
    text = panel._log.toPlainText()
    assert "Hello" in text
    assert "world" in text


def test_cancel_signal(panel, qtbot):
    with qtbot.waitSignal(panel.cancel_requested):
        panel._cancel_btn.show()
        panel._cancel_btn.click()


def test_dnd_internal_mime(panel, tmp_path):
    f1 = tmp_path / "test.txt"
    f2 = tmp_path / "other.py"
    f1.write_text("a")
    f2.write_text("b")
    data = f"{f1}\n{f2}".encode()
    mime = QMimeData()
    mime.setData("application/x-biome-fm-paths", data)
    paths = panel._paths_from_mime(mime)
    assert len(paths) == 2
    assert paths[0] == f1.resolve()


def test_dnd_os_urls(panel, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("x")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(f))])
    paths = panel._paths_from_mime(mime)
    assert paths == [f.resolve()]
