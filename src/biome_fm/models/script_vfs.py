"""extfs-style Script VFS — delegate archive browsing to shell scripts."""
from __future__ import annotations

import io
import shlex
import subprocess
import tomllib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScriptVFSSpec:
    extensions: list[str]
    list_cmd: str    # template: {archive} {dir}
    read_cmd: str    # template: {archive} {path}
    timeout: int = 10


def load_script_vfs_specs(spec_dir: Path) -> list[ScriptVFSSpec]:
    """Load *.toml from spec_dir."""
    if not spec_dir.is_dir():
        return []
    specs = []
    for toml_file in sorted(spec_dir.glob("*.toml")):
        data = tomllib.loads(toml_file.read_text())
        specs.append(ScriptVFSSpec(
            extensions=data.get("extensions", []),
            list_cmd=data["list_cmd"],
            read_cmd=data["read_cmd"],
            timeout=int(data.get("timeout", 10)),
        ))
    return specs


class ScriptVFS:
    """Browse archive-like files via external scripts. Read-only."""

    def __init__(self, archive_path: Path, spec: ScriptVFSSpec) -> None:
        self._archive = archive_path
        self._spec = spec

    def listdir(self, path: Path) -> list:
        from biome_fm.models.file_item import FileItem

        rel = "" if path == self._archive else str(path.relative_to(self._archive))
        cmd = self._spec.list_cmd.format(
            archive=shlex.quote(str(self._archive)),
            dir=shlex.quote(rel),
        )
        try:
            out = subprocess.check_output(
                cmd, shell=True, timeout=self._spec.timeout, text=True, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return []

        items = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            kind, size, mtime_s, name = parts[0], parts[1], parts[2], parts[3]
            vpath = self._archive / (f"{rel}/{name}" if rel else name)
            items.append(FileItem(
                name=name,
                path=vpath,
                is_dir=kind == "d",
                size=int(size) if size.isdigit() else 0,
                modified=float(mtime_s) if mtime_s else 0.0,
            ))
        return items

    def read_bytes(self, path: Path) -> bytes:
        internal = "/".join(path.relative_to(self._archive).parts)
        cmd = self._spec.read_cmd.format(
            archive=shlex.quote(str(self._archive)),
            path=shlex.quote(internal),
        )
        try:
            return subprocess.check_output(
                cmd, shell=True, timeout=self._spec.timeout, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return b""

    @contextmanager
    def open_file(self, path: Path):
        yield io.BytesIO(self.read_bytes(path))
