import pytest


def test_delegate_has_set_filter(qtbot):
    from biome_fm.views.pane_view import PaneView

    pv = PaneView()
    qtbot.addWidget(pv)
    delegate = pv._table.itemDelegate()
    assert hasattr(delegate, "set_filter")
    delegate.set_filter("test")
    assert delegate._filter == "test"
