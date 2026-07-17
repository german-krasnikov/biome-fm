"""Unit tests for swap_panes() and target_equals_source() in ManagerPresenter."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.presenters.manager_presenter import ManagerPresenter


def _make_presenter(path: Path) -> MagicMock:
    p = MagicMock()
    p.current_path = path
    return p


def _manager(left_path: Path, right_path: Path) -> tuple[ManagerPresenter, MagicMock, MagicMock]:
    left = _make_presenter(left_path)
    right = _make_presenter(right_path)
    vfs = MagicMock()
    mgr = ManagerPresenter(left, right, vfs)
    return mgr, left, right


def test_swap_panes_exchanges_paths():
    left_path = Path("/left")
    right_path = Path("/right")
    mgr, left, right = _manager(left_path, right_path)

    mgr.swap_panes()

    left.navigate_to.assert_called_once_with(right_path)
    right.navigate_to.assert_called_once_with(left_path)


def test_target_equals_source_mirrors():
    mgr, left, right = _manager(Path("/active"), Path("/other"))
    # active = "left" by default

    mgr.target_equals_source()

    right.navigate_to.assert_called_once_with(Path("/active"))
    left.navigate_to.assert_not_called()
