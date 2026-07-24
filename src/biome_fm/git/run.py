"""Thin subprocess wrapper for git commands — shared across all git callers."""
from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(
    args: list[str],
    cwd: Path,
    timeout: int = 5,
    check: bool = True,
    safe: bool = False,
) -> str:
    """Run git <args> in cwd. Return stdout.

    safe=True: any error (OSError, FileNotFoundError, TimeoutExpired, CalledProcessError)
               returns "" — implies check=False internally.
    check=True (default, safe=False only): raises CalledProcessError on non-zero exit.
    """
    _check = False if safe else check
    try:
        r = subprocess.run(
            ["git"] + args, cwd=cwd,
            capture_output=True, text=True, timeout=timeout, check=_check,
        )
        return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        if safe:
            return ""
        raise


def git_is_ignored(path: Path, repo: Path, timeout: int = 5) -> bool:
    """Return True if path is git-ignored. Returns False if git unavailable."""
    try:
        r = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=repo, capture_output=True, timeout=timeout,
        )
        return r.returncode == 0
    except OSError:
        return False
