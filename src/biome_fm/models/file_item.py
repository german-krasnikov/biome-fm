"""FileItem — immutable data class for file entries."""

from dataclasses import dataclass
from pathlib import Path

from biome_fm.utils.format import format_size as _format_size


@dataclass(frozen=True, slots=True)
class FileItem:
    name: str
    path: Path
    is_dir: bool
    size: int
    modified: float
    permissions: str = ""
    is_symlink: bool = False
    atime: float = 0.0
    ctime: float = 0.0
    owner: str = ""
    symlink_target: Path | None = None
    is_broken: bool = False

    @property
    def size_str(self) -> str:
        if self.is_dir:
            return "<DIR>"
        return _format_size(self.size)
