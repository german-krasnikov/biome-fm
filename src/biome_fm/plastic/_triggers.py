"""Triggers backend — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Trigger

_FMT = "{id}|{name}|{event}|{filter}|{command}"


def parse_triggers(output: str) -> list[Trigger]:
    items = []
    for line in output.splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 5:
            items.append(Trigger(
                trigger_id=parts[0],
                name=parts[1],
                event=parts[2],
                filter=parts[3],
                command="|".join(parts[4:]),  # command may contain pipes
            ))
    return items


def list_triggers(cwd: Path) -> list[Trigger]:
    out = run_cm(["trigger", "list", f"--format={_FMT}"], cwd=cwd, safe=True)
    return parse_triggers(out)


def create_trigger(name: str, event: str, filter_: str, command: str, cwd: Path) -> None:
    run_cm(["trigger", "create", event, name, filter_, command], cwd=cwd)


def delete_trigger(trigger_id: str, cwd: Path) -> None:
    run_cm(["trigger", "delete", trigger_id], cwd=cwd)
