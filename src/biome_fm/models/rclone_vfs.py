"""RcloneVFS — VFS backed by rclone subprocess (F240).

ponytail: subprocess-per-call is O(n) connections for n file ops;
replace with rclone serve when throughput matters.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from biome_fm.models.file_item import FileItem

_NANO_RE = re.compile(r"(\.\d{6})\d+Z$")


def _parse_modtime(s: str) -> float:
    """Parse rclone ModTime string (may have nanoseconds) to epoch float."""
    s = _NANO_RE.sub(r"\1+00:00", s)
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).timestamp()


def _parse_entry(entry: dict, base_path: Path) -> FileItem:
    name = entry["Name"]
    return FileItem(
        name=name,
        path=base_path / name,
        is_dir=entry.get("IsDir", False),
        size=max(entry.get("Size", 0), 0),
        modified=_parse_modtime(entry.get("ModTime", "1970-01-01T00:00:00Z")),
    )


class RcloneVFS:
    """VFS backed by rclone subprocess. Requires rclone in PATH."""

    @staticmethod
    def available() -> bool:
        return shutil.which("rclone") is not None

    def __init__(self, remote: str) -> None:
        """remote: e.g. 'gdrive:' or 's3:mybucket'"""
        if not self.available():
            raise RuntimeError("rclone not found in PATH")
        self._remote = remote

    def _rclone_path(self, path: Path) -> str:
        """Combine remote name with path: 'gdrive:/subdir'"""
        return self._remote + str(path)

    def listdir(self, path: Path) -> list[FileItem]:
        out = subprocess.check_output(
            ["rclone", "lsjson", self._rclone_path(path)], text=True
        )
        return [_parse_entry(e, path) for e in json.loads(out)]

    def copy(self, src: Path, dst: Path) -> None:
        subprocess.check_call(
            ["rclone", "copyto", str(src), self._rclone_path(dst)]
        )

    def delete(self, path: Path) -> None:
        subprocess.check_call(["rclone", "deletefile", self._rclone_path(path)])

    def mkdir(self, path: Path) -> None:
        subprocess.check_call(["rclone", "mkdir", self._rclone_path(path)])

    def read_bytes(self, path: Path) -> bytes:
        return subprocess.check_output(
            ["rclone", "cat", self._rclone_path(path)]
        )

    def write_bytes(self, path: Path, data: bytes) -> None:
        proc = subprocess.run(
            ["rclone", "rcat", self._rclone_path(path)],
            input=data,
            check=True,
        )
