"""Unit tests for ManagerPresenter mirror mode. No Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.presenters.manager_presenter import ManagerPresenter


def _fake_pane(path: Path):
    p = MagicMock()
    p.current_path = path
    p.navigate_calls: list[Path] = []

    def _nav(dest: Path) -> None:
        p.current_path = dest
        p.navigate_calls.append(dest)

    p.navigate_to.side_effect = _nav
    return p


@pytest.fixture
def mp():
    left = _fake_pane(Path("/left"))
    right = _fake_pane(Path("/right"))
    m = ManagerPresenter(left=left, right=right, vfs=MagicMock())
    return m, left, right


class TestMirrorMode:
    def test_mirror_default_off(self, mp):
        m, _, _ = mp
        assert m.mirror is False

    def test_toggle_mirror(self, mp):
        m, _, _ = mp
        m.toggle_mirror()
        assert m.mirror is True
        m.toggle_mirror()
        assert m.mirror is False

    def test_mirror_navigates_other_pane(self, mp):
        m, left, right = mp
        m.toggle_mirror()
        m.navigate_active(Path("/new"))
        assert Path("/new") in left.navigate_calls
        assert Path("/new") in right.navigate_calls

    def test_mirror_both_directions(self, mp):
        m, left, right = mp
        m.set_active_pane("right")
        m.toggle_mirror()
        m.navigate_active(Path("/sync"))
        assert Path("/sync") in right.navigate_calls
        assert Path("/sync") in left.navigate_calls

    def test_mirror_no_infinite_recurse(self, mp):
        """Reentrancy guard prevents recursive mirroring."""
        m, left, right = mp
        m.toggle_mirror()
        # Should not raise RecursionError
        m.navigate_active(Path("/safe"))
        # Each pane called exactly once
        assert left.navigate_calls.count(Path("/safe")) == 1
        assert right.navigate_calls.count(Path("/safe")) == 1

    def test_mirror_off_no_sync(self, mp):
        m, left, right = mp
        m.navigate_active(Path("/solo"))
        assert Path("/solo") in left.navigate_calls
        assert right.navigate_calls == []
