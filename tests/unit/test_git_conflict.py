"""Unit tests for git conflict_ops — pure Python, no Qt, no real git repo."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.git.conflict_ops import (
    ConflictMarker,
    ConflictRegion,
    conflicted_files,
    find_conflict_markers,
    parse_conflict_regions,
)

_CONFLICT_TEXT = """\
normal line 1
normal line 2
<<<<<<< HEAD
ours line A
ours line B
=======
theirs line X
>>>>>>> feature-branch
normal line 3
"""

_TWO_CONFLICTS = """\
<<<<<<< HEAD
ours 1
=======
theirs 1
>>>>>>> branch1
middle
<<<<<<< HEAD
ours 2
=======
theirs 2
>>>>>>> branch2
"""


# ---------------------------------------------------------------------------
# conflicted_files
# ---------------------------------------------------------------------------

def test_find_conflicted_files_parses_unmerged():
    fake_output = "foo.py\nbar.txt\n"
    with patch("biome_fm.git.conflict_ops.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=fake_output, returncode=0)
        result = conflicted_files(Path("/repo"))
    assert result == ["foo.py", "bar.txt"]


def test_no_conflicts_returns_empty():
    with patch("biome_fm.git.conflict_ops.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = conflicted_files(Path("/repo"))
    assert result == []


def test_not_git_repo_returns_empty():
    with patch("biome_fm.git.conflict_ops.subprocess.run", side_effect=FileNotFoundError):
        result = conflicted_files(Path("/not/a/repo"))
    assert result == []


# ---------------------------------------------------------------------------
# find_conflict_markers
# ---------------------------------------------------------------------------

def test_find_conflict_markers_in_file(tmp_path: Path):
    f = tmp_path / "conflict.txt"
    f.write_text(_CONFLICT_TEXT)
    markers = find_conflict_markers(f)
    assert len(markers) == 3
    assert markers[0] == ConflictMarker(line=3, marker="<<<<<<<", label="HEAD")
    assert markers[1] == ConflictMarker(line=6, marker="=======", label="")
    assert markers[2] == ConflictMarker(line=8, marker=">>>>>>>", label="feature-branch")


def test_find_conflict_markers_clean_file(tmp_path: Path):
    f = tmp_path / "clean.py"
    f.write_text("x = 1\ny = 2\n")
    assert find_conflict_markers(f) == []


def test_find_conflict_markers_missing_file():
    assert find_conflict_markers(Path("/nonexistent/file.py")) == []


def test_find_conflict_markers_binary_file(tmp_path: Path):
    f = tmp_path / "binary.bin"
    f.write_bytes(b"\x00\x01\x02\x03")
    assert find_conflict_markers(f) == []


# ---------------------------------------------------------------------------
# parse_conflict_regions
# ---------------------------------------------------------------------------

def test_parse_conflict_sections(tmp_path: Path):
    f = tmp_path / "conflict.txt"
    f.write_text(_CONFLICT_TEXT)
    regions = parse_conflict_regions(f)
    assert len(regions) == 1
    r = regions[0]
    assert r.start == 3
    assert r.separator == 6
    assert r.end == 8
    assert r.ours == ["ours line A", "ours line B"]
    assert r.theirs == ["theirs line X"]


def test_parse_conflict_regions_two_conflicts(tmp_path: Path):
    f = tmp_path / "two.txt"
    f.write_text(_TWO_CONFLICTS)
    regions = parse_conflict_regions(f)
    assert len(regions) == 2
    assert regions[0].ours == ["ours 1"]
    assert regions[0].theirs == ["theirs 1"]
    assert regions[1].ours == ["ours 2"]
    assert regions[1].theirs == ["theirs 2"]


def test_parse_conflict_regions_clean_file(tmp_path: Path):
    f = tmp_path / "clean.py"
    f.write_text("a = 1\n")
    assert parse_conflict_regions(f) == []
