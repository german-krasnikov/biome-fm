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


def test_parse_btn_disabled_while_loading(qtbot: QtBot, dialog: NLOpsDialog) -> None:
    """_on_parse must disable parse_btn before submitting to pool."""
    from biome_fm.qt import QPushButton
    parse_btn = dialog.findChild(QPushButton, "parse_btn")
    dialog._input.setText("copy x.txt to y/")

    submitted: list[bool] = []
    original_submit = dialog._pool.submit

    def _intercepted(fn, *args):
        submitted.append(parse_btn.isEnabled())
        return original_submit(fn, *args)

    dialog._pool.submit = _intercepted
    parse_btn.click()
    assert submitted == [False]  # disabled before submit


def test_drain_updates_ui_after_parse(qtbot: QtBot, tmp_path: Path) -> None:
    """NLOpsDialog._drain() updates status and enables execute on success."""
    from biome_fm.presenters.nl_ops_presenter import NLOperation
    from biome_fm.qt import QPushButton

    dlg = NLOpsDialog(provider=object(), cwd=tmp_path)
    qtbot.addWidget(dlg)

    op = NLOperation(
        description="copy x to y",
        op="copy",
        sources=[tmp_path / "x"],
        destination=tmp_path / "y",
    )
    dlg._result_q.put(op)
    dlg._drain()

    exec_btn = dlg.findChild(QPushButton, "execute_btn")
    assert exec_btn.isEnabled()
    assert "copy x to y" in dlg._status.text()
