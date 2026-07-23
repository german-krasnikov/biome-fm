"""Docker Container VFS — browse container filesystem via docker CLI."""
from __future__ import annotations

import io
import shutil
import subprocess
import tarfile
from contextlib import contextmanager
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.models.ls_parser import parse_ls_line


def _docker_available() -> bool:
    return shutil.which("docker") is not None


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
        items = []
        for line in out.splitlines():
            info = parse_ls_line(line)
            if info is None:
                continue
            name = info["name"].split(" -> ")[0]  # strip symlink target
            if name in (".", ".."):
                continue
            items.append(FileItem(
                name=name, path=path / name,
                is_dir=info["is_dir"], size=info["size"], modified=info["mtime"],
            ))
        return items

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
