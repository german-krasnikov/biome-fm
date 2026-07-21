"""F444 — xattr Browser tests."""
from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="xattr not on Windows")


@pytest.fixture
def file_item(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("hello")
    s = p.stat()
    from biome_fm.models.file_item import FileItem
    return FileItem(name="test.txt", path=p, is_dir=False, size=s.st_size, modified=s.st_mtime)


def test_xattr_tab_exists(qtbot, file_item):
    from biome_fm.views.properties_dialog import PropertiesDialog
    dlg = PropertiesDialog(file_item)
    qtbot.addWidget(dlg)
    tabs = dlg._tabs
    labels = [tabs.tabText(i) for i in range(tabs.count())]
    assert "Extended Attrs" in labels


def test_xattr_table_populated(qtbot, file_item, monkeypatch):
    import os
    monkeypatch.setattr(os, "listxattr", lambda path, follow_symlinks=True: ["user.test"], raising=False)
    monkeypatch.setattr(os, "getxattr", lambda path, key, follow_symlinks=True: b"hello", raising=False)

    from biome_fm.views.properties_dialog import PropertiesDialog
    dlg = PropertiesDialog(file_item)
    qtbot.addWidget(dlg)

    assert dlg._xattr_table.rowCount() == 1
    assert dlg._xattr_table.item(0, 0).text() == "user.test"
    assert dlg._xattr_table.item(0, 1).text() == "hello"


def test_add_xattr_row(qtbot, file_item, monkeypatch):
    import os
    monkeypatch.setattr(os, "listxattr", lambda path, follow_symlinks=True: [], raising=False)

    from biome_fm.views.properties_dialog import PropertiesDialog
    dlg = PropertiesDialog(file_item)
    qtbot.addWidget(dlg)

    assert dlg._xattr_table.rowCount() == 0
    # find Add button and click it
    from PySide6.QtWidgets import QPushButton
    add_btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Add")
    add_btn.click()
    assert dlg._xattr_table.rowCount() == 1
