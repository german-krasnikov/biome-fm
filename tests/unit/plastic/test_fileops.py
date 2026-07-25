"""Unit tests for _fileops.py — add(), remove(), move()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._fileops import add, remove, move


def test_add_calls_cm_add_with_paths(tmp_path):
    p = tmp_path / "a.py"
    with patch("biome_fm.plastic._fileops.run_cm") as m:
        add([p], tmp_path)
    m.assert_called_once_with(["add", str(p)], cwd=tmp_path)


def test_add_recursive_flag(tmp_path):
    p = tmp_path / "a.py"
    with patch("biome_fm.plastic._fileops.run_cm") as m:
        add([p], tmp_path, recursive=True)
    args = m.call_args.args[0]
    assert "--recursive" in args
    assert str(p) in args


def test_remove_calls_cm_remove(tmp_path):
    p = tmp_path / "a.py"
    with patch("biome_fm.plastic._fileops.run_cm") as m:
        remove(p, tmp_path)
    m.assert_called_once_with(["remove", str(p)], cwd=tmp_path)


def test_move_calls_cm_move_with_src_dst(tmp_path):
    src = tmp_path / "a.py"
    dst = tmp_path / "b.py"
    with patch("biome_fm.plastic._fileops.run_cm") as m:
        move(src, dst, tmp_path)
    m.assert_called_once_with(["move", str(src), str(dst)], cwd=tmp_path)
