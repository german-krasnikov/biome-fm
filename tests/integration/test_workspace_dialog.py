"""Integration tests for WorkspaceDialog."""
from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot

from biome_fm.models.workspace_store import WorkspaceStore
from biome_fm.views.workspace_dialog import WorkspaceDialog


@pytest.fixture
def store(tmp_path):
    s = WorkspaceStore(tmp_path / "workspaces.json")
    s.save("alpha", ["/a"], ["/b"])
    s.save("beta", ["/c"], ["/d"])
    return s


def test_dialog_shows_names(qtbot, store):
    dlg = WorkspaceDialog(store)
    qtbot.addWidget(dlg)
    items = [dlg._list.item(i).text() for i in range(dlg._list.count())]
    assert items == ["alpha", "beta"]


def test_save_emits_signal(qtbot, store, monkeypatch):
    dlg = WorkspaceDialog(store)
    qtbot.addWidget(dlg)
    monkeypatch.setattr(
        "biome_fm.views.workspace_dialog.QInputDialog.getText",
        lambda *a, **kw: ("my_ws", True),
    )
    with qtbot.waitSignal(dlg.save_requested, timeout=1000) as blocker:
        dlg._btn_save.click()
    assert blocker.args == ["my_ws"]


def test_delete_emits_signal(qtbot, store):
    dlg = WorkspaceDialog(store)
    qtbot.addWidget(dlg)
    dlg._list.setCurrentRow(0)
    with qtbot.waitSignal(dlg.delete_requested, timeout=1000) as blocker:
        dlg._btn_delete.click()
    assert blocker.args == ["alpha"]
