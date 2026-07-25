"""Unit tests for _find.find_files — RED phase."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._find import find_files  # type: ignore[import]


def test_find_files_calls_cm(tmp_path):
    with patch("biome_fm.plastic._find.run_cm", return_value="") as mock_cm:
        find_files("*.py", tmp_path)
    mock_cm.assert_called_once()
    args = mock_cm.call_args[0][0]
    assert args[0] == "find"
    assert any("*.py" in a for a in args)


def test_find_files_returns_paths(tmp_path):
    mock_output = "/repo/src/a.py\n/repo/src/b.py\n"
    with patch("biome_fm.plastic._find.run_cm", return_value=mock_output):
        result = find_files("*.py", tmp_path)
    assert result == [Path("/repo/src/a.py"), Path("/repo/src/b.py")]


def test_find_files_empty(tmp_path):
    with patch("biome_fm.plastic._find.run_cm", return_value=""):
        result = find_files("*.py", tmp_path)
    assert result == []


def test_find_files_pattern_with_quote(tmp_path):
    with patch("biome_fm.plastic._find.run_cm", return_value="") as mock_cm:
        find_files("it's", tmp_path)
    args = mock_cm.call_args[0][0]
    where = [a for a in args if "like" in a][0]
    assert "it''s" in where
