"""Custom toolbar that loads actions from CommandRegistry."""
from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QToolBar

from biome_fm.commands.registry import CommandRegistry


class CustomToolBar(QToolBar):
    def __init__(self, registry: CommandRegistry, parent=None) -> None:
        super().__init__(parent)
        self._registry = registry

    def load_actions(self, action_ids: list[str]) -> None:
        self.clear()
        for aid in action_ids:
            try:
                entry = self._registry.get_entry(aid)
                act = QAction(entry.name, self)
                if entry.shortcut:
                    act.setShortcut(QKeySequence(entry.shortcut))
                act.triggered.connect(lambda _, e=entry: e.callback())
                self.addAction(act)
            except KeyError:
                pass
