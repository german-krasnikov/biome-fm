"""Unit tests for PlasticPlugin — hookimpls, _find_repo, cm-not-installed guard.

RED: biome_fm.plastic._plugin does not exist yet.
These tests define the contract the implementation must satisfy.

Expected interface:
    class PlasticPlugin:
        BIOME_FM_API_VERSION: tuple[int, int] = (1, 0)

        @staticmethod
        def _find_repo(path: Path) -> Path | None
            # Walk up from path until a dir containing ".plastic" is found.
            # Returns that dir or None.

        @hookimpl
        def on_navigate(self, path: Path) -> None
            # Detect repo; cache result; no-op if not a plastic workspace.
            # Must not raise even if cm is unavailable.

        @hookimpl
        def context_menu_actions(
            self, items: list, pane_id: str
        ) -> list[ActionSpec]
            # Return Plastic actions (checkin, diff, …) when in a repo.
            # Return [] when no repo detected or cm unavailable.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plugins.types import ActionSpec

from biome_fm.plastic._plugin import PlasticPlugin  # type: ignore[import]


# ── _find_repo ────────────────────────────────────────────────────────────────

def test_find_repo_returns_none_outside_plastic_workspace(tmp_path):
    assert PlasticPlugin._find_repo(tmp_path) is None


def test_find_repo_returns_root_when_plastic_dir_present(tmp_path):
    (tmp_path / ".plastic").mkdir()
    assert PlasticPlugin._find_repo(tmp_path) == tmp_path


def test_find_repo_walks_up(tmp_path):
    (tmp_path / ".plastic").mkdir()
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert PlasticPlugin._find_repo(deep) == tmp_path


def test_find_repo_stops_at_fs_root(tmp_path):
    # No .plastic anywhere; must not loop forever
    result = PlasticPlugin._find_repo(tmp_path)
    assert result is None


def test_find_repo_does_not_follow_symlinks_outside_workspace(tmp_path):
    # .plastic must be an actual directory, not just anything named .plastic
    (tmp_path / ".plastic").write_text("not a dir")
    result = PlasticPlugin._find_repo(tmp_path)
    assert result is None  # .plastic file, not directory


# ── API version ───────────────────────────────────────────────────────────────

def test_plugin_has_api_version():
    assert hasattr(PlasticPlugin, "BIOME_FM_API_VERSION")
    major, _minor = PlasticPlugin.BIOME_FM_API_VERSION
    assert major == 1


# ── on_navigate ───────────────────────────────────────────────────────────────

def test_on_navigate_does_not_raise_outside_repo(tmp_path):
    plugin = PlasticPlugin()
    plugin.on_navigate(path=tmp_path)  # must not raise


def test_on_navigate_does_not_raise_when_cm_unavailable(tmp_path):
    (tmp_path / ".plastic").mkdir()
    plugin = PlasticPlugin()
    with patch("subprocess.run", side_effect=FileNotFoundError("no cm")):
        plugin.on_navigate(path=tmp_path)  # must not raise


def test_on_navigate_detects_repo(tmp_path):
    (tmp_path / ".plastic").mkdir()
    plugin = PlasticPlugin()
    plugin.on_navigate(path=tmp_path)
    # After navigating into a repo, the plugin should know we're in one
    assert plugin._current_repo == tmp_path


def test_on_navigate_clears_repo_on_exit(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".plastic").mkdir(parents=True)
    outside = tmp_path / "other"
    outside.mkdir()

    plugin = PlasticPlugin()
    plugin.on_navigate(path=repo)
    assert plugin._current_repo == repo

    plugin.on_navigate(path=outside)
    assert plugin._current_repo is None


# ── context_menu_actions ──────────────────────────────────────────────────────

def test_context_menu_no_repo_returns_empty(tmp_path):
    plugin = PlasticPlugin()
    plugin.on_navigate(path=tmp_path)  # no .plastic dir
    actions = plugin.context_menu_actions(items=[], pane_id="left")
    assert actions == []


def test_context_menu_in_repo_returns_actions(tmp_path):
    (tmp_path / ".plastic").mkdir()
    plugin = PlasticPlugin()
    plugin.on_navigate(path=tmp_path)
    actions = plugin.context_menu_actions(items=["fake_item"], pane_id="left")
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, ActionSpec) for a in actions)


def test_context_menu_actions_have_labels(tmp_path):
    (tmp_path / ".plastic").mkdir()
    plugin = PlasticPlugin()
    plugin.on_navigate(path=tmp_path)
    actions = plugin.context_menu_actions(items=["fake_item"], pane_id="left")
    labels = {a.label for a in actions}
    # At minimum, expect a diff or checkin action
    assert any("diff" in lbl.lower() or "check" in lbl.lower() for lbl in labels)


def test_context_menu_returns_actions_even_when_cm_unavailable(tmp_path):
    # context_menu_actions does NOT call cm — actions are always shown when in a
    # repo. The cm guard lives in _open_window(), which is the action callback.
    (tmp_path / ".plastic").mkdir()
    plugin = PlasticPlugin()
    plugin.on_navigate(path=tmp_path)
    actions = plugin.context_menu_actions(items=["item"], pane_id="left")
    assert len(actions) >= 1  # basic actions (Plastic SCM…, Checkin…) always present
