"""FileItem — immutable data class for file entries."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileItem:
    name: str
    path: Path
    is_dir: bool
    size: int
    modified: float
    permissions: str = ""

    @property
    def size_str(self) -> str:
        if self.is_dir:
            return "<DIR>"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if self.size < 1024:
                return f"{self.size:.0f} {unit}" if unit == "B" else f"{self.size:.1f} {unit}"
            self.size  # frozen — can't modify, so:
        # unfrozen workaround via local
        s = self.size
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if s < 1024:
                return f"{s:.1f} {unit}"
            s /= 1024
        return f"{s:.1f} PB"
