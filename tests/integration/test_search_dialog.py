"""SearchDialog integration tests."""
from pathlib import Path

import pytest

from biome_fm.presenters.search_presenter import SearchMode


@pytest.fixture
def dialog(qtbot):
    from biome_fm.views.search_dialog import SearchDialog
    dlg = SearchDialog(Path("/home/user"))
    qtbot.addWidget(dlg)
    dlg.show()
    return dlg


def test_dialog_creation(dialog):
    assert dialog.windowTitle() == "Find Files"
    assert dialog._query.text() == ""


def test_query_property(dialog):
    dialog._query.setText("*.txt")
    assert dialog.query == "*.txt"


def test_query_strips_whitespace(dialog):
    dialog._query.setText("  *.txt  ")
    assert dialog.query == "*.txt"


def test_mode_defaults_to_wildcard(dialog):
    assert dialog.mode == SearchMode.NAME_WILDCARD


def test_mode_regex(dialog):
    dialog._mode.setCurrentIndex(1)
    assert dialog.mode == SearchMode.NAME_REGEX


def test_mode_content(dialog):
    dialog._mode.setCurrentIndex(2)
    assert dialog.mode == SearchMode.CONTENT


def test_max_results_default(dialog):
    assert dialog.max_results == 1000


def test_max_results_set(dialog):
    dialog._max_results.setValue(500)
    assert dialog.max_results == 500


def test_empty_query_does_not_accept(dialog):
    dialog._query.setText("")
    dialog._on_accept()
    assert dialog.result() != dialog.DialogCode.Accepted


def test_whitespace_query_does_not_accept(dialog):
    dialog._query.setText("   ")
    dialog._on_accept()
    assert dialog.result() != dialog.DialogCode.Accepted


def test_valid_query_accepts(dialog):
    dialog._query.setText("*.py")
    dialog._on_accept()
    assert dialog.result() == dialog.DialogCode.Accepted


def test_root_shown_in_label(qtbot):
    from biome_fm.qt import QLabel
    from biome_fm.views.search_dialog import SearchDialog
    dlg = SearchDialog(Path("/custom/path"))
    qtbot.addWidget(dlg)
    labels = dlg.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]
    assert any("/custom/path" in t for t in texts)


def test_get_params_cancel_returns_none(qtbot):
    from biome_fm.qt import QTimer
    from biome_fm.views.search_dialog import SearchDialog
    dlg = SearchDialog(Path("/tmp"))
    qtbot.addWidget(dlg)
    QTimer.singleShot(0, dlg.reject)
    result = dlg.exec()
    assert result != SearchDialog.DialogCode.Accepted
