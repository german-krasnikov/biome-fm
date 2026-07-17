"""User-defined shell commands loaded from TOML."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


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
        lines: list[str] = []
        for c in self._commands:
            lines.append("[[commands]]")
            lines.append(f'id = "{c.id}"')
            lines.append(f'label = "{c.label}"')
            lines.append(f'command = "{c.command}"')
            if c.shortcut:
                lines.append(f'shortcut = "{c.shortcut}"')
            lines.append("")
        self._path.write_text("\n".join(lines))

    def add(self, cmd: UserCommand) -> None:
        self._commands = [c for c in self._commands if c.id != cmd.id]
        self._commands.append(cmd)

    def remove(self, cmd_id: str) -> None:
        self._commands = [c for c in self._commands if c.id != cmd_id]
