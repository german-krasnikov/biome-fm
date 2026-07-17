"""Integration tests: SearchDialog + SearchTemplateStore."""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from pytestqt.qtbot import QtBot

from biome_fm.models.search_template_store import SearchTemplate, SearchTemplateStore
from biome_fm.qt import QComboBox
from biome_fm.views.search_dialog import SearchDialog


def test_dialog_shows_template_combo_when_store_provided(
    qtbot: QtBot, tmp_path: Path
) -> None:
    store = SearchTemplateStore(tmp_path / "t.toml")
    store.save(SearchTemplate(name="py", pattern="*.py", mode="wildcard"))

    dlg = SearchDialog(Path("/"), store=store)
    qtbot.addWidget(dlg)

    combos = dlg.findChildren(QComboBox)
    # At minimum the template combo must be present (mode combo also exists)
    template_combos = [c for c in combos if c.itemText(0) == "-- no template --"]
    assert len(template_combos) == 1
    # Template name visible in combo
    assert template_combos[0].count() == 2  # "-- no template --" + "py"


def test_no_template_bar_when_store_is_none(qtbot: QtBot) -> None:
    dlg = SearchDialog(Path("/"), store=None)
    qtbot.addWidget(dlg)

    combos = dlg.findChildren(QComboBox)
    template_combos = [c for c in combos if c.itemText(0) == "-- no template --"]
    assert len(template_combos) == 0
