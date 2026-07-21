"""Read-only VFS for ISO 9660 disc images via pycdlib."""
from __future__ import annotations

import io
from contextlib import contextmanager
from pathlib import Path

from biome_fm.models.file_item import FileItem

try:
    import pycdlib as _pycdlib
    _HAS_PYCDLIB = True
except ImportError:
    _pycdlib = None  # type: ignore[assignment]
    _HAS_PYCDLIB = False


class IsoVFS:
    def __init__(self, iso_path: Path) -> None:
        if not _HAS_PYCDLIB:
            raise ImportError("Install pycdlib: pip install pycdlib")
        self._iso_path = iso_path
        self._iso = _pycdlib.PyCdlib()
        self._iso.open(str(iso_path))

    def _to_iso_path(self, path: Path) -> str:
        if path == self._iso_path:
            return "/"
        return "/" + "/".join(path.relative_to(self._iso_path).parts)

    def listdir(self, path: Path) -> list[FileItem]:
        iso_dir = self._to_iso_path(path)
        items = []
        for child in self._iso.list_children(iso_path=iso_dir):
            name = child.file_identifier.decode(errors="replace").rstrip(";1")
            if name in (".", "..") or not name:
                continue
            is_dir = child.isdir
            size = 0 if is_dir else child.data_length
            items.append(FileItem(name=name, path=path / name, is_dir=is_dir, size=size, modified=0.0))
        return items

    def read_bytes(self, path: Path) -> bytes:
        out = io.BytesIO()
        self._iso.get_file_from_iso_fp(out, iso_path=self._to_iso_path(path))
        return out.getvalue()

    @contextmanager
    def open_file(self, path: Path):
        yield io.BytesIO(self.read_bytes(path))

    def close(self) -> None:
        self._iso.close()
