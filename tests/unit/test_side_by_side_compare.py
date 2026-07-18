"""TDD: F220 — Side-by-Side File Compare dialog."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QTextBrowser

from biome_fm.views.diff_view_dialog import DiffViewDialog

_SAMPLE_DIFF = (
    "--- a/file.txt\n+++ b/file.txt\n@@ -1,3 +1,3 @@\n"
    " context line\n-removed line\n+added line\n context2\n"
)


def test_diff_dialog_has_two_panes(qtbot) -> None:
    dlg = DiffViewDialog(_SAMPLE_DIFF)
    qtbot.addWidget(dlg)
    assert len(dlg.findChildren(QTextBrowser)) == 2


def test_diff_lines_colored(qtbot) -> None:
    dlg = DiffViewDialog(_SAMPLE_DIFF)
    qtbot.addWidget(dlg)
    left_html = dlg.left_browser.toHtml()
    assert "removed line" in left_html
    assert "added line" not in left_html
    # Red color applied
    assert "ff6b6b" in left_html or "color" in left_html.lower()


def test_right_pane_has_added_lines(qtbot) -> None:
    dlg = DiffViewDialog(_SAMPLE_DIFF)
    qtbot.addWidget(dlg)
    right_html = dlg.right_browser.toHtml()
    assert "added line" in right_html
    assert "removed line" not in right_html


def test_empty_diff_shows_identical_message(qtbot) -> None:
    dlg = DiffViewDialog("")
    qtbot.addWidget(dlg)
    assert len(dlg.findChildren(QTextBrowser)) == 2
    combined = dlg.left_browser.toHtml() + dlg.right_browser.toHtml()
    assert "identical" in combined.lower()
