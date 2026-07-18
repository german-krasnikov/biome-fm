"""Multi-rename presenter — pure Python, no Qt."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from biome_fm.models.file_item import FileItem


class RenameRule(Enum):
    REGEX = "regex"
    COUNTER = "counter"
    EXTENSION = "extension"


@dataclass
class RenamePreview:
    original: str
    new_name: str
    conflict: bool = False


class RenamePresenter:
    """Computes rename previews for a fixed list of items. No Qt."""

    def __init__(self, items: list[FileItem]) -> None:
        self._items = items
        self._previews: list[RenamePreview] = []

    # ── apply rules ────────────────────────────────────────────────────────

    def apply_regex(self, pattern: str, replacement: str, flags: int = 0) -> list[RenamePreview]:
        try:
            new_names = [re.sub(pattern, replacement, it.name, flags=flags) for it in self._items]
        except re.error:
            new_names = [it.name for it in self._items]
        return self._save(new_names)

    def apply_counter(self, template: str, start: int = 1, step: int = 1) -> list[RenamePreview]:
        try:
            new_names = [
                template.format(n=start + i * step) + Path(it.name).suffix
                for i, it in enumerate(self._items)
            ]
        except (KeyError, IndexError, ValueError):
            new_names = [it.name for it in self._items]
        return self._save(new_names)

    def apply_extension(self, new_ext: str) -> list[RenamePreview]:
        ext = new_ext.lstrip(".")
        new_names = [
            it.name if it.is_dir else Path(it.name).stem + "." + ext
            for it in self._items
        ]
        return self._save(new_names)

    # ── output ─────────────────────────────────────────────────────────────

    def get_renames(self, previews: list[RenamePreview]) -> list[tuple[Path, Path]]:
        """Return (old, new) pairs, excluding conflicts and unchanged names."""
        return [
            (it.path, it.path.parent / pv.new_name)
            for it, pv in zip(self._items, previews, strict=True)
            if not pv.conflict and pv.new_name != it.name
        ]

    @property
    def has_conflicts(self) -> bool:
        return any(p.conflict for p in self._previews)

    # ── internal ────────────────────────────────────────────────────────────

    def _save(self, new_names: list[str]) -> list[RenamePreview]:
        counts = Counter(new_names)
        self._previews = [
            RenamePreview(original=it.name, new_name=name, conflict=counts[name] > 1)
            for it, name in zip(self._items, new_names, strict=True)
        ]
        return self._previews
