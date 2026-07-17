"""Integration tests for TransferQueuePanel display."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication, QProgressBar, QPushButton

from biome_fm.views.transfer_queue_panel import TransferQueuePanel


@pytest.fixture
def panel(qtbot):
    cancelled = []
    p = TransferQueuePanel(cancel_cb=lambda tid: cancelled.append(tid))
    qtbot.addWidget(p)
    p.show()
    QApplication.processEvents()
    return p, cancelled


def test_shows_row_on_op_started(panel):
    p, _ = panel
    p.on_op_started(1, "Copy 2 item(s)")
    assert p._rows.get(1) is not None


def test_progress_bar_updates(panel):
    p, _ = panel
    p.on_op_started(1, "Copy")
    p.on_op_progress(1, files_done=2, files_total=10, bytes_done=200, bytes_total=1000, current_file="file.txt")
    bar = p._rows[1].findChild(QProgressBar)
    assert bar.value() == 200
    assert bar.maximum() == 1000


def test_cancel_button_functional(panel):
    p, cancelled = panel
    p.on_op_started(42, "Move files")
    btn = p._rows[42].findChild(QPushButton)
    assert btn is not None
    btn.click()
    assert 42 in cancelled
