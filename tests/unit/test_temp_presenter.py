"""Unit tests for temp_presenter — TDD red phase first."""
from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _make_entry(name: str, size: int = 100, mtime_offset: float = 0) -> MagicMock:
    """Build a fake os.DirEntry."""
    e = MagicMock(spec=os.DirEntry)
    e.name = name
    e.path = f"/tmp/{name}"
    stat = MagicMock()
    stat.st_size = size
    stat.st_mtime = time.time() - mtime_offset
    e.stat.return_value = stat
    return e


def test_list_entries_finds_files():
    from biome_fm.presenters.temp_presenter import TempEntry, list_temp_entries

    fake = [_make_entry("foo.tmp", 512, 86400), _make_entry("bar.log", 256, 0)]
    with patch("os.scandir", return_value=iter(fake)):
        result = list_temp_entries()
    assert len(result) == 2
    assert all(isinstance(r, TempEntry) for r in result)
    assert result[0].path == Path("/tmp/foo.tmp")
    assert result[0].size == 512
    assert result[0].age_days == pytest.approx(1.0, abs=0.1)


def test_list_entries_skips_permission_error():
    from biome_fm.presenters.temp_presenter import list_temp_entries

    bad = _make_entry("locked.tmp")
    bad.stat.side_effect = PermissionError("nope")
    good = _make_entry("ok.tmp", 100, 0)

    with patch("os.scandir", return_value=iter([bad, good])):
        result = list_temp_entries()
    assert len(result) == 1
    assert result[0].path == Path("/tmp/ok.tmp")


def test_delete_entries_removes_files(tmp_path: Path):
    from biome_fm.presenters.temp_presenter import TempEntry, delete_entries

    f1 = tmp_path / "a.tmp"
    f2 = tmp_path / "b.tmp"
    f1.write_text("x")
    f2.write_text("y")

    entries = [TempEntry(f1, 1, 0.0), TempEntry(f2, 1, 0.0)]
    count = delete_entries(entries)

    assert count == 2
    assert not f1.exists()
    assert not f2.exists()


def test_delete_entries_skips_missing(tmp_path: Path):
    from biome_fm.presenters.temp_presenter import TempEntry, delete_entries

    ghost = tmp_path / "gone.tmp"
    # doesn't exist — should not raise
    count = delete_entries([TempEntry(ghost, 0, 0.0)])
    assert count == 0
