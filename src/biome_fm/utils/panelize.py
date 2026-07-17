"""panelize — parse shell stdout lines into FileItems."""
from __future__ import annotations

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
