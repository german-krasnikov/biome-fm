"""Integration tests for PaneView column visibility."""
import pytest


def test_set_hidden_columns(qtbot):
    from biome_fm.models.directory_model import COL_EXT, COL_SIZE
    from biome_fm.views.pane_view import PaneView

    pv = PaneView()
    qtbot.addWidget(pv)
    pv.set_hidden_columns(["Ext"])
    assert pv._table.horizontalHeader().isSectionHidden(COL_EXT)
    assert not pv._table.horizontalHeader().isSectionHidden(COL_SIZE)


def test_unhide_all(qtbot):
    from biome_fm.models.directory_model import COL_EXT
    from biome_fm.views.pane_view import PaneView

    pv = PaneView()
    qtbot.addWidget(pv)
    pv.set_hidden_columns(["Ext"])
    pv.set_hidden_columns([])
    assert not pv._table.horizontalHeader().isSectionHidden(COL_EXT)
