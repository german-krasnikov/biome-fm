"""TDD tests for RsyncCmd (F427 — rsync delta-transfer backend)."""
from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.commands.rsync_cmd import RsyncCmd, rsync_available
from biome_fm.operations.task import Cancelled


# ---------------------------------------------------------------------------
# rsync_available
# ---------------------------------------------------------------------------

def test_rsync_available_true(monkeypatch):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: "/usr/bin/rsync")
    assert rsync_available() is True


def test_rsync_available_false(monkeypatch):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: None)
    assert rsync_available() is False


# ---------------------------------------------------------------------------
# execute
# ---------------------------------------------------------------------------

def _make_proc(stdout_lines=(), returncode=0):
    proc = MagicMock()
    proc.stdout = iter(stdout_lines)
    proc.wait.return_value = returncode
    proc.returncode = returncode
    return proc


def test_rsync_unavailable_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: None)
    src = tmp_path / "a.txt"
    src.touch()
    cmd = RsyncCmd([src], tmp_path / "dst", threading.Event(), lambda *a: None)
    with pytest.raises(RuntimeError, match="rsync not found"):
        cmd.execute()


def test_rsync_cmd_execute_success(monkeypatch, tmp_path):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: "/usr/bin/rsync")
    src = tmp_path / "file.txt"
    src.touch()
    dest = tmp_path / "dst"
    dest.mkdir()

    proc = _make_proc(stdout_lines=[], returncode=0)
    with patch("biome_fm.commands.rsync_cmd.subprocess.Popen", return_value=proc):
        cmd = RsyncCmd([src], dest, threading.Event(), lambda *a: None)
        cmd.execute()

    assert cmd._created == [dest / "file.txt"]


def test_rsync_cmd_progress_reported(monkeypatch, tmp_path):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: "/usr/bin/rsync")
    src = tmp_path / "file.txt"
    src.touch()
    dest = tmp_path / "dst"
    dest.mkdir()

    # rsync --progress line format: "    1,234,567  42%   12.34MB/s  ..."
    progress_line = "    1,234,567  42%   12.34MB/s    0:00:01"
    proc = _make_proc(stdout_lines=[progress_line], returncode=0)

    reports = []
    with patch("biome_fm.commands.rsync_cmd.subprocess.Popen", return_value=proc):
        cmd = RsyncCmd([src], dest, threading.Event(), lambda *a: reports.append(a))
        cmd.execute()

    assert any(r[2] == 42 for r in reports)


def test_rsync_cmd_cancel(monkeypatch, tmp_path):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: "/usr/bin/rsync")
    src = tmp_path / "file.txt"
    src.touch()
    dest = tmp_path / "dst"
    dest.mkdir()

    cancel = threading.Event()
    cancel.set()  # pre-cancelled

    proc = _make_proc(stdout_lines=["    100  50%   1MB/s"], returncode=0)
    with patch("biome_fm.commands.rsync_cmd.subprocess.Popen", return_value=proc):
        cmd = RsyncCmd([src], dest, cancel, lambda *a: None)
        with pytest.raises(Cancelled):
            cmd.execute()

    proc.terminate.assert_called_once()


def test_rsync_cmd_nonzero_exit_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("biome_fm.commands.rsync_cmd.shutil.which", lambda _: "/usr/bin/rsync")
    src = tmp_path / "file.txt"
    src.touch()
    dest = tmp_path / "dst"
    dest.mkdir()

    proc = _make_proc(stdout_lines=[], returncode=23)
    with patch("biome_fm.commands.rsync_cmd.subprocess.Popen", return_value=proc):
        cmd = RsyncCmd([src], dest, threading.Event(), lambda *a: None)
        with pytest.raises(OSError, match="rsync failed"):
            cmd.execute()


# ---------------------------------------------------------------------------
# undo
# ---------------------------------------------------------------------------

def test_rsync_cmd_undo(tmp_path):
    dest = tmp_path / "dst"
    dest.mkdir()
    f = dest / "file.txt"
    f.write_text("x")

    cmd = RsyncCmd([], dest, threading.Event(), lambda *a: None)
    cmd._created = [f]
    cmd.undo()

    assert not f.exists()
    assert cmd._created == []


def test_rsync_cmd_undo_dir(tmp_path):
    dest = tmp_path / "dst"
    dest.mkdir()
    d = dest / "subdir"
    d.mkdir()
    (d / "inner.txt").write_text("y")

    cmd = RsyncCmd([], dest, threading.Event(), lambda *a: None)
    cmd._created = [d]
    cmd.undo()

    assert not d.exists()


# ---------------------------------------------------------------------------
# description
# ---------------------------------------------------------------------------

def test_rsync_cmd_description_singular(tmp_path):
    src = tmp_path / "a.txt"
    cmd = RsyncCmd([src], tmp_path, threading.Event(), lambda *a: None)
    assert cmd.description == "Rsync 1 item"


def test_rsync_cmd_description_plural(tmp_path):
    sources = [tmp_path / f"{i}.txt" for i in range(3)]
    cmd = RsyncCmd(sources, tmp_path, threading.Event(), lambda *a: None)
    assert cmd.description == "Rsync 3 items"
