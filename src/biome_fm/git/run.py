"""Thin subprocess wrapper for git commands — shared across all git callers."""
from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path, timeout: int = 5, check: bool = True) -> str:
    """Run git <args> in cwd. Return stdout. Raise subprocess.CalledProcessError on non-zero."""
    r = subprocess.run(
        ["git"] + args, cwd=cwd,
        capture_output=True, text=True, timeout=timeout, check=check,
    )
    return r.stdout
