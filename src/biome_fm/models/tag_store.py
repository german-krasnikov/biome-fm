"""TOML-backed file tag store. No Qt dependencies."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from biome_fm.models._store_base import toml_escape as _esc
from biome_fm.utils.atomic_write import atomic_write


@dataclass
class TagStore:
    _path: Path
    _tags: dict[str, list[str]] = field(default_factory=dict)   # str(path) → [tag, ...]
    _colors: dict[str, str] = field(default_factory=dict)        # tag → "#hex"

    @classmethod
    def load(cls, path: Path) -> TagStore:
        if not path.exists():
            return cls(_path=path)
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except (OSError, ValueError, tomllib.TOMLDecodeError):
            return cls(_path=path)
        return cls(
            _path=path,
            _tags=dict(data.get("tags", {})),
            _colors=dict(data.get("colors", {})),
        )

    def save(self) -> None:
        lines: list[str] = ["[tags]\n"]
        for p, tags in self._tags.items():
            tag_list = ", ".join(f'"{_esc(t)}"' for t in tags)
            lines.append(f'"{_esc(p)}" = [{tag_list}]\n')
        lines.append("\n[colors]\n")
        for tag, color in self._colors.items():
            lines.append(f'"{_esc(tag)}" = "{color}"\n')
        atomic_write(self._path, "".join(lines))

    def get_tags(self, path: Path) -> list[str]:
        return list(self._tags.get(str(path), []))

    def set_tags(self, path: Path, tags: list[str]) -> None:
        if tags:
            self._tags[str(path)] = list(tags)
        else:
            self._tags.pop(str(path), None)

    def tag_color(self, tag: str) -> str | None:
        return self._colors.get(tag)

    def set_tag_color(self, tag: str, color: str) -> None:
        self._colors[tag] = color

    def all_tags(self) -> list[str]:
        seen: set[str] = set()
        for tags in self._tags.values():
            seen.update(tags)
        return sorted(seen)

    def paths_for_tag(self, tag: str) -> list[Path]:
        return [Path(p) for p, tags in self._tags.items() if tag in tags]
