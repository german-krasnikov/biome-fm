"""Integration tests for TempPanel dialog."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.presenters.temp_presenter import TempEntry


@pytest.fixture()
def fake_entries(tmp_path: Path):
    return [
        TempEntry(tmp_path / "old.tmp", 1024, 10.0),
        TempEntry(tmp_path / "new.tmp", 512, 1.0),
    ]


def test_panel_shows_entries(qtbot, fake_entries):
    from biome_fm.views.temp_panel import TempPanel

    with patch("biome_fm.views.temp_panel.list_temp_entries", return_value=fake_entries):
        panel = TempPanel()
        qtbot.addWidget(panel)

    assert panel._table.rowCount() == 2
    assert panel._table.item(0, 0).text() == "old.tmp"
    assert panel._table.item(1, 0).text() == "new.tmp"


def test_delete_old_button_works(qtbot, fake_entries, tmp_path):
    from biome_fm.views.temp_panel import TempPanel

    # Create real files so delete_entries can work
    (tmp_path / "old.tmp").write_text("x")
    (tmp_path / "new.tmp").write_text("y")

    calls = []

    with patch("biome_fm.views.temp_panel.list_temp_entries", return_value=fake_entries):
        panel = TempPanel()
        qtbot.addWidget(panel)

    panel.deleted.connect(calls.append)

    # After clicking "Delete >7 days", only old.tmp (age=10) should be deleted
    with patch("biome_fm.views.temp_panel.list_temp_entries", return_value=[]):
        panel._btn_old.click()

    assert calls == [1]
    assert not (tmp_path / "old.tmp").exists()
    assert (tmp_path / "new.tmp").exists()
