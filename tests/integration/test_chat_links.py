"""Integration tests for path hyperlinks in ChatLog."""
import pytest
from PySide6.QtCore import QUrl

from biome_fm.views._chat_log import ChatLog


@pytest.fixture
def log(qtbot):
    w = ChatLog()
    qtbot.addWidget(w)
    w.show()
    return w


def test_path_link_signal(log):
    received: list[str] = []
    log.path_link_clicked.connect(received.append)
    log._on_anchor_clicked(QUrl("biome:/Users/german/Work/file.py"))
    assert received == ["/Users/german/Work/file.py"]
