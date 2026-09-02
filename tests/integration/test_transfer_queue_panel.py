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


def test_progress_over_2gib_no_overflow(qtbot) -> None:
    from biome_fm.views.transfer_queue_panel import TransferQueuePanel

    p = TransferQueuePanel(cancel_cb=lambda _: None)
    qtbot.addWidget(p)
    p.on_op_started(1, "Copy big.iso")
    # 3 GiB done of 4 GiB — should be 750 permille
    p.on_op_progress(1, 1, 1, 3 * 2**30, 4 * 2**30, "big.iso")
    bar = p._rows[1].findChild(QProgressBar)
    assert bar.maximum() == 1000
    assert bar.value() == 750


def test_progress_dialog_over_2gib_no_overflow(qtbot) -> None:
    from unittest.mock import MagicMock

    from biome_fm.views.progress_dialog import ProgressDialog

    dlg = ProgressDialog(1, "Move 4GB file")
    qtbot.addWidget(dlg)
    event = MagicMock()
    event.current_file = "big.iso"
    event.bytes_total = 4 * 2**30
    event.bytes_done = 3 * 2**30
    event.files_done = 1
    event.files_total = 1
    dlg.update_progress(event)  # must not raise
    assert dlg._bytes_bar.maximum() == 1000
    assert dlg._bytes_bar.value() == 750
