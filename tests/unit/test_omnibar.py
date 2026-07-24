"""Unit tests for OmnibarPresenter and OmniBar view — F411."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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


# --- Item #34: FRECENCY mode ---

def test_mode_for_frecency(presenter):
    assert presenter.mode_for(":docs") == OmniMode.FRECENCY
    assert presenter.mode_for(":") == OmniMode.FRECENCY


def test_frecency_items_no_store(presenter):
    items = presenter.query_changed(":")
    assert items == []


def test_frecency_items_filters(tmp_path, registry):
    from biome_fm.models.frecency_store import FrecencyStore
    from biome_fm.presenters.omnibar_presenter import OmnibarPresenter
    store = FrecencyStore(tmp_path / "f.json")
    store.record(Path("/home/user/projects"))
    store.record(Path("/home/user/docs"))
    p = OmnibarPresenter(registry, frecency=store)
    items = p.query_changed(":doc")
    assert len(items) == 1
    assert items[0].data == Path("/home/user/docs")


def test_frecency_items_no_filter_returns_all(tmp_path, registry):
    from biome_fm.models.frecency_store import FrecencyStore
    from biome_fm.presenters.omnibar_presenter import OmnibarPresenter
    store = FrecencyStore(tmp_path / "f.json")
    store.record(Path("/a"))
    store.record(Path("/b"))
    p = OmnibarPresenter(registry, frecency=store)
    items = p.query_changed(":")
    assert len(items) == 2


def test_existing_modes_unchanged(presenter):
    assert presenter.mode_for(">copy") == OmniMode.COMMAND
    assert presenter.mode_for("/usr") == OmniMode.NAVIGATE
    assert presenter.mode_for("hello") == OmniMode.SEARCH


# --- Item #35: PROJECT mode ---

def test_mode_for_project(presenter):
    assert presenter.mode_for("@") == OmniMode.PROJECT
    assert presenter.mode_for("@bio") == OmniMode.PROJECT


def test_project_items_no_store(presenter):
    items = presenter.query_changed("@")
    assert items == []


def test_project_items_filters_non_projects(tmp_path, registry):
    from biome_fm.models.frecency_store import FrecencyStore
    store = FrecencyStore(tmp_path / "f.json")
    proj = tmp_path / "myapp"
    proj.mkdir()
    (proj / "pyproject.toml").write_text("")
    plain = tmp_path / "downloads"
    plain.mkdir()
    store.record(proj)
    store.record(plain)
    p = OmnibarPresenter(registry, frecency=store)
    items = p.query_changed("@")
    assert len(items) == 1
    assert items[0].data == proj
    assert items[0].label == "myapp"
    assert "python" in items[0].subtitle


def test_project_items_query_filter(tmp_path, registry):
    from biome_fm.models.frecency_store import FrecencyStore
    store = FrecencyStore(tmp_path / "f.json")
    for name in ("biome-fm", "other-app"):
        d = tmp_path / name
        d.mkdir()
        (d / "pyproject.toml").write_text("")
        store.record(d)
    p = OmnibarPresenter(registry, frecency=store)
    items = p.query_changed("@bio")
    assert len(items) == 1
    assert items[0].label == "biome-fm"


def test_project_items_data_is_project_root_not_subdir(tmp_path, registry):
    """Frecency may record a subdir; data must be the project root, not the subdir."""
    from biome_fm.models.frecency_store import FrecencyStore
    store = FrecencyStore(tmp_path / "f.json")
    proj = tmp_path / "myapp"
    subdir = proj / "src" / "components"
    subdir.mkdir(parents=True)
    (proj / "pyproject.toml").write_text("")
    store.record(subdir)  # record a subdir, not the project root
    p = OmnibarPresenter(registry, frecency=store)
    items = p.query_changed("@")
    assert len(items) == 1
    assert items[0].data == proj        # must be project root
    assert items[0].label == "myapp"
    assert str(proj) in items[0].subtitle   # subtitle shows root, not subdir


def test_project_items_deduplicates_same_root(tmp_path, registry):
    """Multiple frecency entries under the same project produce one result."""
    from biome_fm.models.frecency_store import FrecencyStore
    store = FrecencyStore(tmp_path / "f.json")
    proj = tmp_path / "myapp"
    (proj / "src").mkdir(parents=True)
    (proj / "tests").mkdir()
    (proj / "pyproject.toml").write_text("")
    store.record(proj / "src")
    store.record(proj / "tests")
    p = OmnibarPresenter(registry, frecency=store)
    items = p.query_changed("@")
    assert len(items) == 1
    assert items[0].data == proj


def test_project_mode_does_not_break_others(presenter):
    assert presenter.mode_for(":docs") == OmniMode.FRECENCY
    assert presenter.mode_for(">copy") == OmniMode.COMMAND
    assert presenter.mode_for("/usr") == OmniMode.NAVIGATE
