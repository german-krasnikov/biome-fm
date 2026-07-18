"""Sync session profile store — TOML persistence, mirrors SSHProfileStore pattern."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


def _esc(v: str) -> str:
    """Escape backslash and double-quote for a TOML basic string."""
    return v.replace("\\", "\\\\").replace('"', '\\"')


@dataclass
class SyncProfile:
    name: str
    src: str
    dst: str
    exclude: list[str] = field(default_factory=list)
    mirror: bool = False


class SyncProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._profiles: dict[str, SyncProfile] = {}

    def load(self) -> None:
        if not self._path.exists():
            return
        data = tomllib.loads(self._path.read_text())
        for name, v in data.get("profiles", {}).items():
            self._profiles[name] = SyncProfile(
                name=name,
                src=v.get("src", ""),
                dst=v.get("dst", ""),
                exclude=list(v.get("exclude", [])),
                mirror=bool(v.get("mirror", False)),
            )

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for p in self._profiles.values():
            lines.append(f"[profiles.{p.name}]")
            lines.append(f'src = "{_esc(p.src)}"')
            lines.append(f'dst = "{_esc(p.dst)}"')
            excl = ", ".join(f'"{_esc(e)}"' for e in p.exclude)
            lines.append(f"exclude = [{excl}]")
            lines.append(f"mirror = {str(p.mirror).lower()}")
            lines.append("")
        self._path.write_text("\n".join(lines))

    def add(self, profile: SyncProfile) -> None:
        self._profiles[profile.name] = profile

    def get(self, name: str) -> SyncProfile:
        if name not in self._profiles:
            raise KeyError(name)
        return self._profiles[name]

    def delete(self, name: str) -> None:
        if name not in self._profiles:
            raise KeyError(name)
        del self._profiles[name]

    def list_all(self) -> list[SyncProfile]:
        return list(self._profiles.values())
