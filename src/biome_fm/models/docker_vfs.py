"""Docker Container VFS — browse container filesystem via docker CLI."""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import tarfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from biome_fm.models.file_item import FileItem

_LS_RE = re.compile(
    r'^([dl\-][rwx\-]{9})\s+\d+\s+\S+\s+\S+\s+(\d+)\s+'
    r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)$'
)


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _parse_docker_ls(stdout: str, parent: Path) -> list[FileItem]:
    items = []
    for line in stdout.splitlines():
        m = _LS_RE.match(line)
        if not m:
            continue
        mode_str, size, date, time_, name = m.groups()
        name = name.strip().split(" -> ")[0]
        if name in (".", ".."):
            continue
        is_dir = mode_str[0] == "d"
        mtime = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M").timestamp()
        items.append(FileItem(
            name=name, path=parent / name,
            is_dir=is_dir, size=int(size), modified=mtime,
        ))
    return items


class DockerVFS:
    def __init__(self, container_id: str) -> None:
        if not _docker_available():
            raise RuntimeError("docker CLI not found in PATH")
        self._id = container_id

    def _exec(self, *cmd: str, timeout: int = 10) -> str:
        result = subprocess.run(
            ["docker", "exec", self._id, *cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            raise OSError(result.stderr.strip())
        return result.stdout

    def listdir(self, path: Path) -> list[FileItem]:
        out = self._exec("ls", "-la", "--time-style=long-iso", str(path))
        return _parse_docker_ls(out, path)

    def read_bytes(self, path: Path) -> bytes:
        result = subprocess.run(
            ["docker", "cp", f"{self._id}:{path}", "-"],
            capture_output=True, timeout=60,
        )
        if result.returncode != 0:
            raise OSError(result.stderr.decode().strip())
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tf:
            member = next(iter(tf.getmembers()), None)
            if member is None:
                return b""
            f = tf.extractfile(member)
            return f.read() if f else b""

    @contextmanager
    def open_file(self, path: Path):
        yield io.BytesIO(self.read_bytes(path))

    def exists(self, path: Path) -> bool:
        try:
            self._exec("test", "-e", str(path))
            return True
        except OSError:
            return False
