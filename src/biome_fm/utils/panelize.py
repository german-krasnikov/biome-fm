"""panelize — parse shell stdout lines into FileItems."""
from __future__ import annotations

import subprocess
from pathlib import Path

from biome_fm.models.file_item import FileItem


def parse_shell_output(stdout: str, cwd: Path) -> list[FileItem]:
    """Parse stdout lines as file paths. Skip non-existent."""
    items: list[FileItem] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        if not p.is_absolute():
            p = cwd / p
        if not p.exists():
            continue
        stat = p.stat()
        items.append(FileItem(
            name=p.name,
            path=p,
            is_dir=p.is_dir(),
            size=stat.st_size,
            modified=stat.st_mtime,
        ))
    return items


def panelize(cmd: str, cwd: Path) -> list[FileItem]:
    """Run shell command and parse stdout lines as file paths.

    shell=True is intentional: this is the MC-style panelize feature where the
    user supplies an arbitrary shell pipeline (e.g. ``find . -name '*.py'``).
    The command string comes from trusted user input in the UI, not from
    external/untrusted sources.
    """
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=30
    )
    return parse_shell_output(result.stdout, cwd=cwd)
