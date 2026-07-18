"""SelectCriteria — pure-data predicate for multi-criteria file selection (F221)."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

from biome_fm.models.file_item import FileItem


@dataclass
class SelectCriteria:
    name_glob: str = ""
    extensions: list[str] = field(default_factory=list)
    min_size: int = 0   # bytes, 0 = no limit
    max_size: int = 0   # bytes, 0 = no limit
    min_age_days: int = 0
    max_age_days: int = 0

    def matches(self, item: FileItem) -> bool:
        if item.name == "..":
            return False
        if self.name_glob and not fnmatch.fnmatch(item.name, self.name_glob):
            return False
        if self.extensions:
            if Path(item.name).suffix.lower() not in self.extensions:
                return False
        if self.min_size and item.size < self.min_size:
            return False
        if self.max_size and item.size > self.max_size:
            return False
        if item.modified and (self.min_age_days or self.max_age_days):
            import time
            age_days = (time.time() - item.modified) / 86400
            if self.min_age_days and age_days < self.min_age_days:
                return False
            if self.max_age_days and age_days > self.max_age_days:
                return False
        return True
