"""File search via `cm find files`."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm


def find_files(pattern: str, cwd: Path) -> list[Path]:
    # ponytail: name-like only — extend to full where clause builder if needed
    safe = pattern.replace("'", "''")
    out = run_cm(
        ["find", "files", f"where name like '%{safe}%'", "--format={path}"],
        cwd=cwd, safe=True, timeout=30,
    )
    return [Path(line.strip()) for line in out.splitlines() if line.strip()]
