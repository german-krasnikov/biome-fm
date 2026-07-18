"""User-defined context menu actions with JSON persistence."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class UserAction:
    label: str
    command: str
    extensions: list[str] = field(default_factory=list)


class UserActionsStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._actions: list[UserAction] = []

    def add(self, action: UserAction) -> None:
        self._actions.append(action)

    def update(self, idx: int, action: UserAction) -> None:
        self._actions[idx] = action

    def remove(self, idx: int) -> None:
        self._actions.pop(idx)

    def all(self) -> list[UserAction]:
        return list(self._actions)

    def actions_for(self, suffix: str) -> list[UserAction]:
        """Return actions matching suffix, or those with no extension filter."""
        return [a for a in self._actions if not a.extensions or suffix in a.extensions]

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([asdict(a) for a in self._actions], indent=2), encoding="utf-8"
        )

    def load(self) -> None:
        if not self._path.exists():
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        self._actions = [UserAction(**d) for d in data]

    @classmethod
    def load_project(cls, project_root: Path) -> list[UserAction]:
        """Load actions from <project_root>/.biome-fm/actions.json, or [] if absent."""
        candidate = project_root / ".biome-fm" / "actions.json"
        if not candidate.exists():
            return []
        s = cls(candidate)
        s.load()
        return s.all()
