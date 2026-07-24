"""Unit tests for _snapshot_session — pure function, no Qt."""
from pathlib import Path
from unittest.mock import MagicMock


def test_snapshot_session_pure():
    from biome_fm.app import _snapshot_session  # fails until lifted to module level

    coord = MagicMock()
    coord.save_state.return_value = {
        "preview": {"state": "hidden", "float_geometry": ""},
        "ai": {"state": "hidden", "float_geometry": ""},
    }
    left_tabs = MagicMock()
    left_tabs.paths.return_value = [Path("/tmp/a")]
    left_tabs.active_idx = 0
    right_tabs = MagicMock()
    right_tabs.paths.return_value = [Path("/tmp/b")]
    right_tabs.active_idx = 0

    state = _snapshot_session(coord, left_tabs, right_tabs)
    assert state.left.tabs[0].path == "/tmp/a"
    assert state.right.active_idx == 0
    assert state.preview.state == "hidden"
