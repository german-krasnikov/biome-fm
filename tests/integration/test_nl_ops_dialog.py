"""Integration tests for NLOpsDialog — TDD Red phase."""
from __future__ import annotations

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from biome_fm.ai.provider import NoOpProvider
from biome_fm.views.nl_ops_dialog import NLOpsDialog


@pytest.fixture()
def dialog(qtbot: QtBot) -> NLOpsDialog:
    dlg = NLOpsDialog(provider=NoOpProvider(), cwd=Path("/tmp"))
    qtbot.addWidget(dlg)
    return dlg


def test_dialog_shows_input(dialog: NLOpsDialog) -> None:
    from biome_fm.qt import QLineEdit, QPushButton
    assert dialog.findChild(QLineEdit) is not None
    assert dialog.findChild(QPushButton, "parse_btn") is not None


def test_execute_disabled_initially(dialog: NLOpsDialog) -> None:
    from biome_fm.qt import QPushButton
    exec_btn = dialog.findChild(QPushButton, "execute_btn")
    assert exec_btn is not None
    assert not exec_btn.isEnabled()
