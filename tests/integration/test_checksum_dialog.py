"""Integration tests for ChecksumDialog."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QComboBox, QTableWidget  # noqa: E402


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.txt"
    f.write_bytes(b"hello biome")
    return f


class TestChecksumDialog:
    def test_dialog_has_algorithm_selector(self, qtbot, sample_file: Path) -> None:
        from biome_fm.views.checksum_dialog import ChecksumDialog

        dlg = ChecksumDialog([sample_file])
        qtbot.addWidget(dlg)
        combo = dlg.findChild(QComboBox)
        assert combo is not None
        items = [combo.itemText(i) for i in range(combo.count())]
        assert "xxhash" in items
        assert "md5" in items
        assert "sha256" in items

    def test_compute_shows_results(self, qtbot, sample_file: Path) -> None:
        from biome_fm.views.checksum_dialog import ChecksumDialog

        dlg = ChecksumDialog([sample_file])
        qtbot.addWidget(dlg)
        dlg._compute()
        table = dlg.findChild(QTableWidget)
        assert table is not None
        assert table.rowCount() == 1
        assert table.item(0, 0).text() == sample_file.name
        assert len(table.item(0, 1).text()) > 0
