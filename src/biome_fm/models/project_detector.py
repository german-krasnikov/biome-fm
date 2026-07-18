"""Dev project detection by marker files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_MAKE_TARGET_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_\-./]*)\s*:(?!=)")
_JUST_TARGET_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:(?!=)")

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


def parse_makefile_targets(path: Path) -> list[str]:
    """Return list of targets from a Makefile, excluding variables and .PHONY."""
    targets: list[str] = []
    for line in path.read_text(errors="replace").splitlines():
        m = _MAKE_TARGET_RE.match(line)
        if m:
            targets.append(m.group(1).strip())
    return targets


def parse_justfile_targets(path: Path) -> list[str]:
    """Return list of recipe names from a Justfile."""
    targets: list[str] = []
    for line in path.read_text(errors="replace").splitlines():
        m = _JUST_TARGET_RE.match(line)
        if m:
            targets.append(m.group(1))
    return targets


def detect_project(path: Path) -> ProjectInfo | None:
    for p in [path, *path.parents]:
        for marker, ptype in MARKERS.items():
            if (p / marker).exists():
                return ProjectInfo(type=ptype, root=p, name=p.name)
    return None
