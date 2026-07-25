from __future__ import annotations
from pathlib import Path
from ._cm import run_cm
from ._models import UserInfo, GroupInfo


def parse_users(output: str) -> list[UserInfo]:
    result = []
    for line in output.strip().splitlines():
        parts = line.split("|", maxsplit=1)
        result.append(UserInfo(name=parts[0].strip(), email=parts[1].strip() if len(parts) > 1 else ""))
    return result


def list_users(cwd: Path) -> list[UserInfo]:
    out = run_cm(["users", "list"], cwd=cwd, safe=True)
    return parse_users(out)


def add_user(name: str, email: str, cwd: Path) -> None:
    run_cm(["users", "add", name, email], cwd=cwd)


def delete_user(name: str, cwd: Path) -> None:
    run_cm(["users", "delete", name], cwd=cwd)


def parse_groups(output: str) -> list[GroupInfo]:
    result = []
    for line in output.strip().splitlines():
        parts = line.split("|", maxsplit=1)
        members = tuple(m.strip() for m in parts[1].split(",") if m.strip()) if len(parts) > 1 else ()
        result.append(GroupInfo(name=parts[0].strip(), members=members))
    return result


def list_groups(cwd: Path) -> list[GroupInfo]:
    out = run_cm(["groups", "list"], cwd=cwd, safe=True)
    return parse_groups(out)


def add_group(name: str, cwd: Path) -> None:
    run_cm(["groups", "add", name], cwd=cwd)


def delete_group(name: str, cwd: Path) -> None:
    run_cm(["groups", "delete", name], cwd=cwd)


def add_group_member(group: str, user: str, cwd: Path) -> None:
    run_cm(["groups", "addmember", group, user], cwd=cwd)
