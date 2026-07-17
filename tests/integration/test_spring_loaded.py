"""#71 — Spring-Loaded Folders During Drag: timer navigates into hovered dir."""
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.models.file_item import FileItem
from biome_fm.qt import QMimeData, QModelIndex, Qt, QTimer
from biome_fm.views.dnd_utils import _MIME
from biome_fm.views.pane_view import PaneView, _PaneTableView


def test_hover_triggers_navigate(qtbot):
    """Spring timer fires and emits item_activated for hovered directory."""
    pane = PaneView()
    qtbot.addWidget(pane)

    dir_item = FileItem(name="subdir", path=Path("/tmp/subdir"), is_dir=True, size=0, modified=0.0)
    pane.set_items([dir_item])

    activated = []
    pane.item_activated.connect(lambda item: activated.append(item))

    # Simulate spring: set _drop_hint_row = 0, _spring_row already -1 (different)
    table: _PaneTableView = pane._table
    table._drop_hint_row = 0
    table._spring_row = -1

    # Manually trigger what dragMoveEvent would do: start spring on row 0
    table._spring_row = 0
    table._spring_timer.setInterval(0)  # fire immediately
    table._spring_timer.start()

    qtbot.waitUntil(lambda: len(activated) > 0, timeout=1000)
    assert activated[0].name == "subdir"
