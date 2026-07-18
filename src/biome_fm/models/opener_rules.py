"""Declarative file-opener rules (F098)."""
from __future__ import annotations

import fnmatch
import shlex
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OpenerRule:
    match: str  # glob pattern
    cmd: str    # command template with {}


def load_rules(path: Path) -> list[OpenerRule]:
    if not path.exists():
        return []
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return [OpenerRule(r["match"], r["cmd"]) for r in data.get("rule", [])]


def find_opener(rules: list[OpenerRule], filename: str) -> str | None:
    for rule in rules:
        if fnmatch.fnmatch(filename.lower(), rule.match.lower()):
            return rule.cmd
    return None


def apply_cmd(cmd: str, path: Path, selected: list[Path]) -> str:
    """Expand $f/$d/$s and {} placeholders in opener command (F264)."""
    f = shlex.quote(str(path))
    d = shlex.quote(str(path.parent))
    s = " ".join(shlex.quote(str(p)) for p in selected) if selected else f
    return cmd.replace("$f", f).replace("$d", d).replace("$s", s).replace("{}", f)
