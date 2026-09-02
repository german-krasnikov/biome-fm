"""Integration tests: remote events delivered to MainWindow from a worker thread."""
import threading

import pytest
from PySide6.QtWidgets import QApplication

from biome_fm.event_bus import RemoteConnected, bus
from biome_fm.views.main_window import MainWindow


@pytest.fixture
def win(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    yield w
    w.close()


def test_remote_connected_from_thread_updates_label(win, qtbot):
    """RemoteConnected published on a worker thread must reach the GUI label via QueuedConnection."""
    ev = RemoteConnected(scheme="sftp", host="h")

    def publish():
        bus.publish(ev)

    t = threading.Thread(target=publish, daemon=True)
    t.start()
    t.join(timeout=2.0)

    qtbot.wait(50)  # allow queued events to drain
    QApplication.processEvents()

    text = win._remote_status_label.text()
    assert "sftp://h" in text, f"Expected 'sftp://h' in label, got: {text!r}"
