"""Integration tests for SelectByAttrDialog (F221)."""
from __future__ import annotations

import pytest

from biome_fm.views.select_criteria_dialog import SelectByAttrDialog


def test_dialog_has_fields(qtbot) -> None:
    dlg = SelectByAttrDialog()
    qtbot.addWidget(dlg)
    assert hasattr(dlg, "_name_glob")
    assert hasattr(dlg, "_extensions")
    assert hasattr(dlg, "_min_size")
    assert hasattr(dlg, "_max_size")
    assert hasattr(dlg, "_min_age")
    assert hasattr(dlg, "_max_age")


def test_get_criteria_empty(qtbot) -> None:
    dlg = SelectByAttrDialog()
    qtbot.addWidget(dlg)
    c = dlg.get_criteria()
    assert c.name_glob == ""
    assert c.extensions == []
    assert c.min_size == 0
    assert c.max_size == 0


def test_get_criteria_with_values(qtbot) -> None:
    dlg = SelectByAttrDialog()
    qtbot.addWidget(dlg)
    dlg._name_glob.setText("*.py")
    dlg._extensions.setText(".py, .pyi")
    dlg._min_size.setValue(10)   # 10 KB
    c = dlg.get_criteria()
    assert c.name_glob == "*.py"
    assert ".py" in c.extensions
    assert ".pyi" in c.extensions
    assert c.min_size == 10 * 1024
