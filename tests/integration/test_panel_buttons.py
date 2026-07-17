"""Integration tests for shared panel detach+close buttons."""
import pytest


def test_add_panel_buttons_connects(qtbot):
    from biome_fm.qt import QHBoxLayout, QWidget
    from biome_fm.views._panel_buttons import add_panel_buttons

    w = QWidget()
    qtbot.addWidget(w)
    header = QHBoxLayout()
    detach_called = []
    close_called = []
    add_panel_buttons(header, lambda: detach_called.append(1), lambda: close_called.append(1))
    assert header.count() == 2
    header.itemAt(0).widget().click()
    assert detach_called == [1]
    header.itemAt(1).widget().click()
    assert close_called == [1]
