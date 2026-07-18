"""Unit tests for ChmodCmd (F210)."""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_execute_changes_permissions(tmp_path: Path) -> None:
    from biome_fm.commands.chmod_cmd import ChmodCmd

    f = tmp_path / "file.txt"
    f.write_bytes(b"x")
    cmd = ChmodCmd([f], 0o755)
    cmd.execute()
    assert stat.S_IMODE(f.stat().st_mode) == 0o755


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_undo_restores_permissions(tmp_path: Path) -> None:
    from biome_fm.commands.chmod_cmd import ChmodCmd

    f = tmp_path / "file.txt"
    f.write_bytes(b"x")
    original = stat.S_IMODE(f.stat().st_mode)
    cmd = ChmodCmd([f], 0o600)
    cmd.execute()
    assert stat.S_IMODE(f.stat().st_mode) == 0o600
    cmd.undo()
    assert stat.S_IMODE(f.stat().st_mode) == original


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_recursive_chmod(tmp_path: Path) -> None:
    from biome_fm.commands.chmod_cmd import ChmodCmd

    d = tmp_path / "dir"
    d.mkdir()
    f = d / "nested.txt"
    f.write_bytes(b"y")

    cmd = ChmodCmd([d], 0o755, recursive=True)
    cmd.execute()
    assert stat.S_IMODE(d.stat().st_mode) == 0o755
    assert stat.S_IMODE(f.stat().st_mode) == 0o755


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_initial_mode_reads_from_file(tmp_path: Path) -> None:
    from biome_fm.views.permissions_editor_dialog import _initial_mode

    f = tmp_path / "file.txt"
    f.write_bytes(b"x")
    os.chmod(f, 0o640)
    assert _initial_mode([f]) == 0o640


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_initial_mode_fallback(tmp_path: Path) -> None:
    from biome_fm.views.permissions_editor_dialog import _initial_mode

    missing = tmp_path / "no_such_file.txt"
    assert _initial_mode([missing]) == 0o644


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_multiple_files(tmp_path: Path) -> None:
    from biome_fm.commands.chmod_cmd import ChmodCmd

    files = [tmp_path / f"f{i}.txt" for i in range(3)]
    for f in files:
        f.write_bytes(b"z")
    cmd = ChmodCmd(files, 0o644)
    cmd.execute()
    for f in files:
        assert stat.S_IMODE(f.stat().st_mode) == 0o644
