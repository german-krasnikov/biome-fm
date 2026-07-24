"""Tests: Alt+F4 Exit button removed from ActionBar."""
import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.views.action_bar import ActionBar  # noqa: E402


@pytest.fixture()
def bar(qapp):
    return ActionBar()


def test_no_alt_f4_button(bar):
    texts = [
        bar.layout().itemAt(i).widget().text()
        for i in range(bar.layout().count())
    ]
    assert not any("Alt+F4" in t for t in texts)


def test_no_exit_requested_signal(bar):
    assert not hasattr(bar, "exit_requested")
