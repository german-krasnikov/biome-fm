"""Integration tests for markdown rendering in ChatLog bubbles."""
import pytest

from biome_fm.views._chat_log import ChatLog


@pytest.fixture
def log(qtbot):
    w = ChatLog()
    qtbot.addWidget(w)
    w.show()
    return w


def test_user_bubble_plain_text(log):
    log.append_bubble("user", "**bold**")
    assert "**bold**" in log.toPlainText()


def test_assistant_bubble_markdown(log):
    log.append_bubble("assistant", "**bold**")
    html = log.toHtml().lower()
    # Qt may emit <b>, <strong>, or font-weight:700 for bold
    assert "<b>" in html or "<strong>" in html or "font-weight:700" in html


def test_stream_discard_removes_text(log):
    log.stream_start()
    log.stream_token("hello world")
    log.stream_discard()
    assert "hello world" not in log.toPlainText()


def test_thinking_not_merged_with_user(qtbot):
    """Thinking indicator must be in a separate block, left-aligned."""
    from biome_fm.qt import QTextCursor, Qt
    log = ChatLog()
    qtbot.addWidget(log)
    log.append_bubble("user", "hello")
    blocks_before = log.document().blockCount()
    log.show_thinking()
    assert log.document().blockCount() > blocks_before
    cursor = QTextCursor(log.document())
    cursor.setPosition(log._thinking_pos)
    assert cursor.blockFormat().alignment() != Qt.AlignmentFlag.AlignRight


def test_assistant_separate_from_user(qtbot):
    """Assistant bubble must not merge with user bubble."""
    log = ChatLog()
    qtbot.addWidget(log)
    log.append_bubble("user", "ping")
    blocks_after_user = log.document().blockCount()
    log.append_bubble("assistant", "pong")
    assert log.document().blockCount() > blocks_after_user


def test_stream_end_no_ghost_block(qtbot):
    """stream_end should not leave empty blocks before assistant bubble."""
    log = ChatLog()
    qtbot.addWidget(log)
    log.append_bubble("user", "hello")
    log.stream_start()
    log.stream_token("response")
    log.stream_end()
    text = log.toPlainText()
    assert "\n\n\n" not in text
