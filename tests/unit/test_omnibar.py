"""Unit tests for OmnibarPresenter and OmniBar view — F411."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.commands.registry import CommandEntry, CommandRegistry
from biome_fm.presenters.omnibar_presenter import OmniMode, OmnibarPresenter


@pytest.fixture
def registry():
    r = CommandRegistry()
    for name in ("copy", "move", "delete"):
        r.register(CommandEntry(name=name, shortcut="", callback=lambda: None))
    return r


@pytest.fixture
def presenter(registry, tmp_path):
    return OmnibarPresenter(registry, root=tmp_path)


# --- pure-Python tests (no Qt) ---

def test_mode_for_command(presenter):
    assert presenter.mode_for(">copy") == OmniMode.COMMAND


def test_mode_for_navigate(presenter):
    assert presenter.mode_for("/usr") == OmniMode.NAVIGATE
    assert presenter.mode_for("~/doc") == OmniMode.NAVIGATE
    assert presenter.mode_for("./foo") == OmniMode.NAVIGATE


def test_mode_for_search(presenter):
    assert presenter.mode_for("hello") == OmniMode.SEARCH
    assert presenter.mode_for("") == OmniMode.SEARCH


def test_cmd_items_filters(presenter):
    items = presenter.query_changed(">co")
    labels = [i.label for i in items]
    assert "copy" in labels
    assert "delete" not in labels


def test_nav_items_returns_paths(presenter):
    fake = ["/usr/bin", "/usr/local"]
    with patch("biome_fm.presenters.omnibar_presenter.path_completions", return_value=fake):
        items = presenter.query_changed("/usr")
    assert len(items) == 2
    assert items[0].label == "/usr/bin"
    assert items[0].data == Path("/usr/bin")


# --- Qt test ---

def test_omnibar_activate_clears_input(qtbot):
    from biome_fm.commands.registry import CommandRegistry
    from biome_fm.presenters.omnibar_presenter import OmnibarPresenter
    from biome_fm.views.omnibar import OmniBar

    reg = CommandRegistry()
    p = OmnibarPresenter(reg)
    bar = OmniBar(p)
    qtbot.addWidget(bar)

    bar._input.setText("something typed")
    bar.activate(Path.home())
    assert bar._input.text() == ""
