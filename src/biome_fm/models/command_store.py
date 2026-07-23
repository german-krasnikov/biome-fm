"""User-defined shell commands loaded from TOML."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from biome_fm.models._store_base import toml_escape as _esc
from biome_fm.utils.atomic_write import atomic_write


@dataclass
class UserCommand:
    id: str
    label: str
    command: str
    shortcut: str = ""


class CommandStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._commands: list[UserCommand] = []
        self._load()

    @property
    def commands(self) -> list[UserCommand]:
        return list(self._commands)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = tomllib.loads(self._path.read_text())
            for item in data.get("commands", []):
                self._commands.append(UserCommand(
                    id=item["id"],
                    label=item["label"],
                    command=item["command"],
                    shortcut=item.get("shortcut", ""),
                ))
        except Exception:
            pass

    def save(self) -> None:
        e = _esc
        lines: list[str] = []
        for c in self._commands:
            lines.append("[[commands]]")
            lines.append(f'id = "{e(c.id)}"')
            lines.append(f'label = "{e(c.label)}"')
            lines.append(f'command = "{e(c.command)}"')
            if c.shortcut:
                lines.append(f'shortcut = "{e(c.shortcut)}"')
            lines.append("")
        atomic_write(self._path, "\n".join(lines))

    def add(self, cmd: UserCommand) -> None:
        self._commands = [c for c in self._commands if c.id != cmd.id]
        self._commands.append(cmd)

    def remove(self, cmd_id: str) -> None:
        self._commands = [c for c in self._commands if c.id != cmd_id]
