"""cm config helpers — list/set Plastic SCM configuration entries."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import ConfigEntry


def parse_config(output: str) -> list[ConfigEntry]:
    entries: list[ConfigEntry] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        entries.append(ConfigEntry(key=key.strip(), value=value.strip()))
    return entries


def list_config(cwd: Path) -> list[ConfigEntry]:
    out = run_cm(["config", "list"], cwd=cwd, safe=True)
    return parse_config(out)


def set_config(key: str, value: str, cwd: Path) -> None:
    run_cm(["config", "set", key, value], cwd=cwd)
