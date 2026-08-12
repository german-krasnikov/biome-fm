from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import Attribute


def parse_attributes(output: str, obj_spec: str) -> list[Attribute]:
    result = []
    for line in output.strip().splitlines():
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        result.append(Attribute(object_spec=obj_spec, name=name.strip(), value=value.strip()))
    return result


def list_attributes(obj_spec: str, cwd: Path) -> list[Attribute]:
    out = run_cm(["attribute", "list", f"--objectspec={obj_spec}"], cwd=cwd, safe=True)
    return parse_attributes(out, obj_spec)


def set_attribute(obj_spec: str, name: str, value: str, cwd: Path) -> None:
    run_cm(["attribute", "set", f"--objectspec={obj_spec}", f"--name={name}", f"--value={value}"], cwd=cwd)


def delete_attribute(obj_spec: str, name: str, cwd: Path) -> None:
    run_cm(["attribute", "delete", f"--objectspec={obj_spec}", f"--name={name}"], cwd=cwd)
