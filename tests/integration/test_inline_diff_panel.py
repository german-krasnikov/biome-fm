"""Integration tests for InlineDiffPanel and LineNumberedDiffEdit."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtGui import QPixmap

from biome_fm.plastic._components import InlineDiffPanel, LineNumberedDiffEdit


def test_unified_mode_shows_diff(qtbot):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    diff = "@@ -1 +1 @@\n-old\n+new\n"
    panel.show_diff(diff, "test.py")
    assert panel._stack.currentIndex() == 0
    assert "old" in panel._unified_edit.toPlainText()


def test_sbs_toggle_switches_stack(qtbot):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    panel.show_diff("@@ -1 +1 @@\n-a\n+b\n", "x.py")
    panel._mode_sbs.click()
    assert panel._stack.currentIndex() == 1


def test_show_image_loads_pixmap(qtbot, tmp_path):
    px = QPixmap(2, 2)
    path = tmp_path / "img.png"
    px.save(str(path))
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    panel.show_image(path)
    assert panel._stack.currentIndex() == 2
    assert not panel._img_label.pixmap().isNull()


def test_show_binary_sets_label(qtbot):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    panel.show_binary("data.bin")
    assert panel._stack.currentIndex() == 3
    assert "data.bin" in panel._binary_label.text()


def test_default_page_is_placeholder(qtbot):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    assert panel._stack.currentIndex() == 4


def test_clear_resets_to_placeholder(qtbot):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    panel.show_diff("diff text", "f.py")
    panel._mode_sbs.click()
    panel.clear()
    assert panel._stack.currentIndex() == 4
    assert panel._mode_unified.isChecked()


def test_line_numbered_edit_has_gutter(qtbot):
    edit = LineNumberedDiffEdit()
    qtbot.addWidget(edit)
    edit.setPlainText("line1\nline2\nline3")
    assert edit._line_area.width() > 0


def test_filename_label_shows_name(qtbot):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    panel.show_diff("diff", "hello.py")
    assert panel._filename_label.text() == "hello.py"


def test_show_image_null_pixmap_falls_to_binary(qtbot, tmp_path):
    panel = InlineDiffPanel()
    qtbot.addWidget(panel)
    panel.show_image(tmp_path / "nonexistent.png")
    assert panel._stack.currentIndex() == 3
