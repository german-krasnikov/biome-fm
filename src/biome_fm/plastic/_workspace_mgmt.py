"""Workspace & Repo CRUD backend — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm
from ._models import RepoEntry, WorkspaceEntry

_WK_FMT = "{name}|{path}|{server}"
_REPO_FMT = "{name}|{server}"


def parse_workspaces(output: str) -> list[WorkspaceEntry]:
    items = []
    for line in output.splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 3:
            items.append(WorkspaceEntry(name=parts[0], path=Path(parts[1]), server=parts[2]))
    return items


def list_workspaces(cwd: Path) -> list[WorkspaceEntry]:
    out = run_cm(["workspace", "list", f"--format={_WK_FMT}"], cwd=cwd, safe=True)
    return parse_workspaces(out)


def create_workspace(name: str, path: str, server: str, repo: str, cwd: Path) -> None:
    run_cm(
        ["workspace", "create", name, f"--path={path}", f"--server={server}", f"--repository={repo}"],
        cwd=cwd,
    )


def delete_workspace(name: str, cwd: Path) -> None:
    run_cm(["workspace", "delete", name], cwd=cwd)


def parse_repos(output: str) -> list[RepoEntry]:
    items = []
    for line in output.splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 2:
            items.append(RepoEntry(name=parts[0], server=parts[1]))
    return items


def list_repos(cwd: Path) -> list[RepoEntry]:
    out = run_cm(["repo", "list", f"--format={_REPO_FMT}"], cwd=cwd, safe=True)
    return parse_repos(out)


def create_repo(name: str, cwd: Path) -> None:
    run_cm(["repo", "create", name], cwd=cwd)


def delete_repo(name: str, cwd: Path) -> None:
    run_cm(["repo", "delete", name], cwd=cwd)
