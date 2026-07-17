"""Dev project detection by marker files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MARKERS: dict[str, str] = {
    "pyproject.toml": "python",
    "setup.py": "python",
    "package.json": "node",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "pom.xml": "java",
    "build.gradle": "java",
}


@dataclass
class ProjectInfo:
    type: str
    root: Path
    name: str


def detect_project(path: Path) -> ProjectInfo | None:
    for p in [path, *path.parents]:
        for marker, ptype in MARKERS.items():
            if (p / marker).exists():
                return ProjectInfo(type=ptype, root=p, name=p.name)
    return None
