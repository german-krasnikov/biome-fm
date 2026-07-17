"""Integration tests for PropertiesDialog."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.models.file_item import FileItem


def _item(tmp_path: Path, name: str = "test.txt", size: int = 1234) -> FileItem:
    p = tmp_path / name
    p.write_text("x" * size)
    st = p.stat()
    return FileItem(
        name=name,
        path=p,
        is_dir=False,
        size=st.st_size,
        modified=st.st_mtime,
        permissions=oct(st.st_mode)[-3:],
    )


class TestPropertiesDialog:
    def test_shows_file_size(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.properties_dialog import PropertiesDialog

        item = _item(tmp_path, size=1234)
        dlg = PropertiesDialog(item)
        qtbot.addWidget(dlg)
        # size label must contain the numeric value
        assert str(item.size) in dlg._size_label.text()

    def test_shows_file_name(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.properties_dialog import PropertiesDialog

        item = _item(tmp_path, name="myfile.txt")
        dlg = PropertiesDialog(item)
        qtbot.addWidget(dlg)
        assert "myfile.txt" in dlg._name_label.text()

    @pytest.mark.skipif(sys.platform == "win32", reason="no permissions on Windows")
    def test_shows_permissions(self, qtbot, tmp_path: Path) -> None:
        from biome_fm.views.properties_dialog import PropertiesDialog

        item = _item(tmp_path)
        dlg = PropertiesDialog(item)
        qtbot.addWidget(dlg)
        # permissions tab must exist (index 1)
        assert dlg._tabs.count() >= 2
