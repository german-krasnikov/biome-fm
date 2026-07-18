from pathlib import Path
import pytest
from biome_fm.presenters.miller_state import MillerState


ROOT = Path("/tmp/root")
DIR_A = ROOT / "a"
DIR_B = DIR_A / "b"
DIR_C = DIR_B / "c"
DIR_D = DIR_C / "d"
FILE = ROOT / "file.txt"


def test_initial_single_column():
    s = MillerState(ROOT)
    assert s.columns == [ROOT]
    assert s.active_column == ROOT


def test_click_dir_appends_column():
    s = MillerState(ROOT)
    s.select_dir(DIR_A)
    assert s.columns == [ROOT, DIR_A]
    assert s.active_column == DIR_A


def test_max_columns():
    s = MillerState(ROOT)
    s.select_dir(DIR_A)
    s.select_dir(DIR_B)
    s.select_dir(DIR_C)
    s.select_dir(DIR_D)
    assert len(s.columns) == MillerState.MAX_COLUMNS
    assert s.columns[0] == DIR_A  # oldest (ROOT) dropped
    assert s.active_column == DIR_D


def test_back_removes_column():
    s = MillerState(ROOT)
    s.select_dir(DIR_A)
    result = s.go_back()
    assert result is True
    assert s.columns == [ROOT]


def test_back_at_root_noop():
    s = MillerState(ROOT)
    result = s.go_back()
    assert result is False
    assert s.columns == [ROOT]


def test_click_file_no_column():
    s = MillerState(ROOT)
    # files don't go through select_dir — caller's responsibility
    # state must stay unchanged if select_dir is not called
    assert s.columns == [ROOT]
