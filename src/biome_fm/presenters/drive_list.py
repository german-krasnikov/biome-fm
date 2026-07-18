from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QStorageInfo


@dataclass
class VolumeInfo:
    root: Path
    name: str
    free_bytes: int
    total_bytes: int


def list_volumes() -> list[VolumeInfo]:
    """Return mounted volumes using QStorageInfo."""
    return [
        VolumeInfo(
            root=Path(v.rootPath()),
            name=v.displayName() or v.rootPath(),
            free_bytes=v.bytesFree(),
            total_bytes=v.bytesTotal(),
        )
        for v in QStorageInfo.mountedVolumes()
        if v.isValid() and v.isReady()
    ]
