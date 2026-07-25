"""Subprocess wrapper for Plastic SCM cm CLI."""
from __future__ import annotations

import subprocess
from pathlib import Path


class CMError(Exception):
    """cm exited non-zero and safe=False."""


def run_cm(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 10,
    safe: bool = False,
) -> str:
    """Run `cm <args>` in *cwd*, return stdout as str.

    safe=True  — any error (not found, timeout, non-zero exit) returns "".
    safe=False — CMError on non-zero exit; OSError/TimeoutExpired propagate.
    """
    try:
        r = subprocess.run(
            ["cm", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if r.returncode != 0:
            if safe:
                return ""
            raise CMError(r.stderr.strip() or f"cm {args[0]!r} exited {r.returncode}")
        return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        if safe:
            return ""
        raise
