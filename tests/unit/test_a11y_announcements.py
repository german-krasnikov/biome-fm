"""F313 — Status Announcements for Screen Readers."""
from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_set_status_emits_accessible_event(qtbot) -> None:
    from PySide6.QtGui import QAccessible

    from biome_fm.views.pane_view import PaneView

    pane = PaneView()
    qtbot.addWidget(pane)

    with patch.object(QAccessible, "updateAccessibility") as mock_ua:
        pane.set_status("5 files, 0 marked")
        assert mock_ua.called, "set_status must call QAccessible.updateAccessibility"

    assert pane._status_label.text() == "5 files, 0 marked"


def test_set_path_emits_accessible_event(qtbot, tmp_path) -> None:
    from PySide6.QtGui import QAccessible

    from biome_fm.views.pane_view import PaneView

    pane = PaneView()
    qtbot.addWidget(pane)

    with patch.object(QAccessible, "updateAccessibility") as mock_ua:
        pane.set_path(tmp_path)
        assert mock_ua.called, "set_path must call QAccessible.updateAccessibility"
