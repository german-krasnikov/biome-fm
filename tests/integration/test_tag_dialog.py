"""Integration tests for TagDialog."""
import pytest
from pytestqt.qtbot import QtBot

from biome_fm.views.tag_dialog import TagDialog


@pytest.fixture
def dialog(qtbot):
    d = TagDialog(["existing", "keep"], ["existing", "keep", "other"], parent=None)
    qtbot.addWidget(d)
    return d


def test_dialog_shows_tags(dialog):
    labels = [dialog._chip_area.itemAt(i).widget().text()
              for i in range(dialog._chip_area.count())
              if dialog._chip_area.itemAt(i).widget() is not None]
    assert any("existing" in t for t in labels)
    assert any("keep" in t for t in labels)


def test_add_tag(dialog, qtbot):
    dialog._input.setText("newtag")
    qtbot.mouseClick(dialog._btn_add, __import__("biome_fm.qt", fromlist=["Qt"]).Qt.MouseButton.LeftButton)
    labels = [dialog._chip_area.itemAt(i).widget().text()
              for i in range(dialog._chip_area.count())
              if dialog._chip_area.itemAt(i).widget() is not None]
    assert any("newtag" in t for t in labels)
