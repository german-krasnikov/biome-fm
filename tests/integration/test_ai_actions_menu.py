"""Integration tests: AI Actions submenu must wire context_action_requested."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QApplication, QMenu

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _item(path: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=path.name, path=path, size=0, modified=0.0, is_dir=False)


class _NonBlockingMenu(QMenu):
    """QMenu subclass that captures actions instead of blocking in exec()."""

    triggered_action: str | None = None

    def exec(self, *args: object, **kwargs: object) -> None:  # type: ignore[override]
        # Find and fire "Run" from the AI Actions submenu without blocking.
        for act in self.actions():
            if act.text() == "AI Actions":
                sub = act.menu()
                if sub:
                    for sub_act in sub.actions():
                        if sub_act.text() == "Run":
                            sub_act.trigger()
                            return
        return None  # type: ignore[return-value]


class TestAiActionsMenu:
    def test_ai_actions_emit_correct_action_id(
        self, qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Run action in AI Actions submenu must emit context_action_requested('run')."""
        import biome_fm.views.pane_view as pv_mod

        # Replace QMenu in pane_view's namespace so contextMenuEvent builds _NonBlockingMenu
        monkeypatch.setattr(pv_mod, "QMenu", _NonBlockingMenu)

        py_file = tmp_path / "script.py"
        py_file.touch()

        view = PaneView()
        qtbot.addWidget(view)

        view.set_items([_item(py_file)])
        view._table.setCurrentIndex(view._proxy.index(0, 0))

        emitted: list[str] = []
        view.context_action_requested.connect(emitted.append)

        QApplication.sendEvent(
            view._table.viewport(),
            QContextMenuEvent(
                QContextMenuEvent.Reason.Mouse,
                QPoint(5, 5),
                view._table.viewport().mapToGlobal(QPoint(5, 5)),
            ),
        )

        assert emitted == ["run"]
