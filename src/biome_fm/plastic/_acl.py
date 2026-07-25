from __future__ import annotations
from pathlib import Path
from ._cm import run_cm
from ._models import AclEntry


def parse_acl(output: str) -> list[AclEntry]:
    result = []
    for line in output.strip().splitlines():
        parts = line.split("|", maxsplit=2)
        if len(parts) < 3:
            continue
        result.append(AclEntry(principal=parts[0].strip(), kind=parts[1].strip(), permission=parts[2].strip()))
    return result


def get_acl(obj_spec: str, cwd: Path) -> list[AclEntry]:
    out = run_cm(["acl", "get", obj_spec], cwd=cwd, safe=True)
    return parse_acl(out)


def set_acl(obj_spec: str, principal: str, permission: str, cwd: Path) -> None:
    run_cm(["acl", "set", f"--user={principal}", f"--permission={permission}", obj_spec], cwd=cwd)


def delete_acl(obj_spec: str, principal: str, cwd: Path) -> None:
    run_cm(["acl", "delete", f"--user={principal}", obj_spec], cwd=cwd)
