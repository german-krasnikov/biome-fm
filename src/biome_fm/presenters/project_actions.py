"""Dev project action detection (F094)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectAction:
    label: str
    command: str


def detect_actions(directory: Path) -> list[ProjectAction]:
    actions: list[ProjectAction] = []
    if (directory / ".git").is_dir():
        actions.append(ProjectAction("Git Commit", "git commit"))
    if (directory / "pyproject.toml").exists():
        actions += [ProjectAction("Run Tests", "uv run pytest"), ProjectAction("Lint", "ruff check .")]
    if (directory / "package.json").exists():
        actions += [ProjectAction("Install", "npm install"), ProjectAction("Dev Server", "npm run dev")]
    if (directory / "go.mod").exists():
        actions.append(ProjectAction("Build", "go build ./..."))
    return actions
