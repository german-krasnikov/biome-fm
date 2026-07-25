"""Workspace info via `cm wi`."""
from __future__ import annotations

import re
from pathlib import Path

from ._cm import run_cm
from ._models import WorkspaceInfo


def get_workspace_info(cwd: Path) -> WorkspaceInfo:
    out = run_cm(["wi"], cwd=cwd, safe=True)
    if not out.strip():
        return WorkspaceInfo(name=cwd.name, server="", branch="", last_cs=0, wk_path=cwd)

    data: dict[str, str] = {}
    for line in out.splitlines():
        if ": " in line:
            k, _, v = line.partition(": ")
            data[k.strip()] = v.strip()

    # "Workspace name: MyWS@server:8087"
    raw_name = data.get("Workspace name", "")
    name = raw_name.split("@")[0] if "@" in raw_name else raw_name or cwd.name

    server = data.get("Server", "")

    # "Last changeset: 42 on /main@server:8087"
    last_cs_str = data.get("Last changeset", "")
    last_cs = 0
    branch = ""
    if m := re.match(r"(\d+) on ([^@]+)", last_cs_str):
        last_cs = int(m.group(1))
        branch = m.group(2).strip()

    # Fallback: single-line "Branch /main@repo@server" format (some cm versions)
    if not branch:
        if m := re.search(r'Branch\s+(/[^@\s]+)', out):
            branch = m.group(1)

    # If name still unknown (no Workspace name key), extract repo from "Branch /br@repo@server"
    if "Workspace name" not in data:
        if m := re.search(r'Branch\s+/[^@\s]+@([^@\s]+)', out):
            name = m.group(1)

    return WorkspaceInfo(name=name, server=server, branch=branch, last_cs=last_cs, wk_path=cwd)
