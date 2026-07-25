"""Unit tests for run_cm() — subprocess wrapper for the cm CLI."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.plastic._cm import CMError, run_cm


def _proc(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    p = MagicMock()
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


# ── Happy path ────────────────────────────────────────────────────────────────

def test_returns_stdout_on_success(tmp_path):
    with patch("subprocess.run", return_value=_proc(stdout="hello\n")) as m:
        result = run_cm(["status"], cwd=tmp_path)
    assert result == "hello\n"
    m.assert_called_once()


def test_passes_cwd_to_subprocess(tmp_path):
    with patch("subprocess.run", return_value=_proc()) as m:
        run_cm(["status"], cwd=tmp_path)
    assert m.call_args.kwargs["cwd"] == tmp_path


def test_passes_timeout_to_subprocess(tmp_path):
    with patch("subprocess.run", return_value=_proc()) as m:
        run_cm(["status"], cwd=tmp_path, timeout=42)
    assert m.call_args.kwargs["timeout"] == 42


def test_prepends_cm_to_args(tmp_path):
    with patch("subprocess.run", return_value=_proc()) as m:
        run_cm(["find", "changesets"], cwd=tmp_path)
    assert m.call_args.args[0] == ["cm", "find", "changesets"]


# ── Non-zero exit ─────────────────────────────────────────────────────────────

def test_nonzero_safe_false_raises_cmerror(tmp_path):
    with patch("subprocess.run", return_value=_proc(stderr="bad args", returncode=1)):
        with pytest.raises(CMError, match="bad args"):
            run_cm(["status"], cwd=tmp_path, safe=False)


def test_nonzero_empty_stderr_uses_generic_message(tmp_path):
    with patch("subprocess.run", return_value=_proc(returncode=2)):
        with pytest.raises(CMError, match="exited 2"):
            run_cm(["status"], cwd=tmp_path)


def test_nonzero_safe_true_returns_empty(tmp_path):
    with patch("subprocess.run", return_value=_proc(returncode=1)):
        result = run_cm(["status"], cwd=tmp_path, safe=True)
    assert result == ""


# ── cm not installed ──────────────────────────────────────────────────────────

def test_file_not_found_safe_false_propagates(tmp_path):
    with patch("subprocess.run", side_effect=FileNotFoundError("no cm")):
        with pytest.raises(FileNotFoundError):
            run_cm(["status"], cwd=tmp_path, safe=False)


def test_file_not_found_safe_true_returns_empty(tmp_path):
    with patch("subprocess.run", side_effect=FileNotFoundError("no cm")):
        assert run_cm(["status"], cwd=tmp_path, safe=True) == ""


# ── Timeout ───────────────────────────────────────────────────────────────────

def test_timeout_expired_safe_false_propagates(tmp_path):
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["cm"], 10)):
        with pytest.raises(subprocess.TimeoutExpired):
            run_cm(["status"], cwd=tmp_path, safe=False)


def test_timeout_expired_safe_true_returns_empty(tmp_path):
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["cm"], 10)):
        assert run_cm(["status"], cwd=tmp_path, safe=True) == ""


# ── OSError (permission, etc.) ────────────────────────────────────────────────

def test_oserror_safe_false_propagates(tmp_path):
    with patch("subprocess.run", side_effect=OSError("perm denied")):
        with pytest.raises(OSError):
            run_cm(["status"], cwd=tmp_path, safe=False)


def test_oserror_safe_true_returns_empty(tmp_path):
    with patch("subprocess.run", side_effect=OSError("perm denied")):
        assert run_cm(["status"], cwd=tmp_path, safe=True) == ""
