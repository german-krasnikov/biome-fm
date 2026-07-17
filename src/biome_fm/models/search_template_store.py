"""Saved search templates — load/save from TOML."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchTemplate:
    name: str
    pattern: str
    mode: str  # "wildcard" | "regex" | "content"
    max_results: int = 1000


class SearchTemplateStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._templates: list[SearchTemplate] = []
        self._load()

    @property
    def templates(self) -> list[SearchTemplate]:
        return list(self._templates)

    def save(self, t: SearchTemplate) -> None:
        self._templates = [x for x in self._templates if x.name != t.name]
        self._templates.append(t)
        self._persist()

    def delete(self, name: str) -> None:
        self._templates = [x for x in self._templates if x.name != name]
        self._persist()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = tomllib.loads(self._path.read_text())
            for item in data.get("templates", []):
                self._templates.append(SearchTemplate(
                    name=item["name"],
                    pattern=item["pattern"],
                    mode=item.get("mode", "wildcard"),
                    max_results=item.get("max_results", 1000),
                ))
        except Exception:
            pass

    def _persist(self) -> None:
        lines: list[str] = []
        for t in self._templates:
            lines.append("[[templates]]")
            lines.append(f'name = "{t.name}"')
            lines.append(f'pattern = "{t.pattern}"')
            lines.append(f'mode = "{t.mode}"')
            lines.append(f"max_results = {t.max_results}")
            lines.append("")
        self._path.write_text("\n".join(lines))
