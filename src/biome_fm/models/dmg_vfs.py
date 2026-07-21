"""Read-only VFS for macOS DMG images via hdiutil subprocess."""
from __future__ import annotations

import io
import plistlib
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

from biome_fm.models.file_item import FileItem


class DmgVFS:
    def __init__(self, dmg_path: Path) -> None:
        if sys.platform != "darwin":
            raise RuntimeError("DmgVFS requires macOS")
        self._dmg = dmg_path
        self._mount: Path | None = None

    def mount(self) -> None:
        result = subprocess.run(
            ["hdiutil", "attach", str(self._dmg), "-readonly", "-nobrowse", "-plist"],
            capture_output=True, timeout=30, check=True,
        )
        info = plistlib.loads(result.stdout)
        for entity in info.get("system-entities", []):
            if mp := entity.get("mount-point"):
                self._mount = Path(mp)
                return
        raise RuntimeError("hdiutil: no mount point in output")

    def unmount(self) -> None:
        if self._mount:
            subprocess.run(
                ["hdiutil", "detach", str(self._mount)],
                timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self._mount = None

    def _real(self, path: Path) -> Path:
        if self._mount is None:
            raise RuntimeError("Not mounted")
        if path == self._dmg:
            return self._mount
        return self._mount / path.relative_to(self._dmg)

    def listdir(self, path: Path) -> list[FileItem]:
        real = self._real(path)
        items = []
        for child in sorted(real.iterdir()):
            s = child.stat()
            items.append(FileItem(
                name=child.name, path=path / child.name,
                is_dir=child.is_dir(), size=s.st_size, modified=s.st_mtime,
            ))
        return items

    def read_bytes(self, path: Path) -> bytes:
        return self._real(path).read_bytes()

    @contextmanager
    def open_file(self, path: Path):
        yield io.BytesIO(self.read_bytes(path))
