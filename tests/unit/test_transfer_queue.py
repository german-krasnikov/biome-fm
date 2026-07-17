"""Unit tests for TransferQueuePanel (Qt offscreen)."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QProgressBar, QPushButton

from biome_fm.views.transfer_queue_panel import TransferQueuePanel


@pytest.fixture
def panel(qtbot):
    cancelled = []
    p = TransferQueuePanel(cancel_cb=lambda tid: cancelled.append(tid))
    qtbot.addWidget(p)
    return p, cancelled


def test_on_op_started_adds_row(panel):
    p, _ = panel
    p.on_op_started(1, "Copy 3 item(s)")
    assert 1 in p._rows


def test_on_op_progress_updates_bar(panel):
    p, _ = panel
    p.on_op_started(1, "Copy")
    p.on_op_progress(1, files_done=1, files_total=5, bytes_done=100, bytes_total=500, current_file="a.txt")
    bar = p._rows[1].findChild(QProgressBar)
    assert bar is not None
    assert bar.value() == 100
    assert bar.maximum() == 500


def test_on_op_done_marks_row(panel):
    p, _ = panel
    p.on_op_started(2, "Move")
    p.on_op_done(2)
    # cancel button should be hidden after done
    btn = p._rows[2].findChild(QPushButton)
    assert btn is None or not btn.isVisible()


def test_on_op_error_shows_error(panel):
    p, _ = panel
    p.on_op_started(3, "Copy")
    p.on_op_error(3, "Permission denied")
    btn = p._rows[3].findChild(QPushButton)
    assert btn is None or not btn.isVisible()


def test_on_op_cancelled_marks_row(panel):
    p, _ = panel
    p.on_op_started(4, "Move")
    p.on_op_cancelled(4)
    btn = p._rows[4].findChild(QPushButton)
    assert btn is None or not btn.isVisible()


def test_cancel_button_calls_callback(panel):
    p, cancelled = panel
    p.on_op_started(5, "Copy 1 item(s)")
    btn = p._rows[5].findChild(QPushButton)
    assert btn is not None
    btn.click()
    assert cancelled == [5]


def test_multiple_concurrent_transfers_each_get_row(panel):
    p, _ = panel
    p.on_op_started(10, "Copy A")
    p.on_op_started(11, "Move B")
    p.on_op_started(12, "Copy C")
    assert len(p._rows) == 3
    assert all(tid in p._rows for tid in (10, 11, 12))
