"""Plastic SCM lock/unlock operations."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Lock


def _current_branch(cwd: Path) -> str:
    return run_cm(["wi", "--format={workspacebranch}"], cwd=cwd).strip()


def lock(path: Path, cwd: Path) -> None:
    """Acquire exclusive lock on *path*. Raises CMError on failure."""
    branch = _current_branch(cwd)
    run_cm(["lock", "create", f"br:{branch}", str(path)], cwd=cwd)


def unlock(path: Path, cwd: Path) -> None:
    """Release lock on *path*. Raises CMError on failure."""
    run_cm(["lock", "unlock", str(path)], cwd=cwd)


def get_locks(cwd: Path) -> list[Lock]:
    """Return all current locks in the workspace."""
    out = run_cm(["lock", "list", "--machinereadable"], cwd=cwd, safe=True)
    return parse_locks(out)


def parse_locks(output: str) -> list[Lock]:
    """Parse `cm lock list --machinereadable` output (path|owner|branch[|status] per line)."""
    results: list[Lock] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        status = parts[3].strip() if len(parts) > 3 else "Locked"
        results.append(Lock(
            path=Path(parts[0].strip()),
            owner=parts[1].strip(),
            branch=parts[2].strip(),
            status=status,
        ))
    return results
