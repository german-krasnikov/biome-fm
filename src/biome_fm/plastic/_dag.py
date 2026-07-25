"""Branch DAG data loading and layout — pure Python, no Qt."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ._changesets import parse_changesets
from ._cm import run_cm
from ._models import Changeset

_CS_FMT = "{changesetid}|{date}|{owner}|{branch}|{comment}"
_BR_DAG_FMT = "{name}|{parent}|{date}|{owner}"


@dataclass(slots=True)
class BranchNode:
    name: str
    parent: str
    lane: int = 0


@dataclass(slots=True)
class CSGraphRow:
    cs_id: int
    lane: int
    active_lanes: frozenset[int]
    color_idx: int  # lane % _N_GRAPH_COLORS


_N_GRAPH_COLORS = 8  # must match len(_GRAPH_COLORS) in _components.py


@dataclass(slots=True)
class DAGNode:
    cs_id: int
    branch: str
    date: datetime
    x: float
    y: float


def load_dag_data(cwd: Path) -> tuple[list[BranchNode], list[Changeset]]:
    br_out = run_cm(["find", "branches", f"--format={_BR_DAG_FMT}"], cwd=cwd, safe=True)
    cs_out = run_cm(["find", "changesets", f"--format={_CS_FMT}"], cwd=cwd, safe=True)
    return parse_branch_dag(br_out), parse_changesets(cs_out)


def parse_branch_dag(output: str) -> list[BranchNode]:
    result = []
    for line in output.strip().splitlines():
        parts = line.split("|", maxsplit=3)
        if len(parts) < 2:
            continue
        name = parts[0].strip()
        parent = parts[1].strip()
        if not name:
            continue
        result.append(BranchNode(name=name, parent=parent))
    return result


def assign_lanes(branches: list[BranchNode]) -> dict[str, int]:
    """BFS from roots; each branch gets a unique lane index."""
    children: dict[str, list[str]] = {}
    for b in branches:
        children.setdefault(b.parent, []).append(b.name)

    names = {b.name for b in branches}
    roots = [b.name for b in branches if not b.parent or b.parent not in names]
    if not roots and branches:
        roots = [branches[0].name]

    lanes: dict[str, int] = {}
    lane = 0
    queue = deque(roots)
    while queue:
        name = queue.popleft()
        if name in lanes:
            continue
        lanes[name] = lane
        lane += 1
        for child in children.get(name, []):
            queue.append(child)

    for b in branches:
        if b.name not in lanes:
            lanes[b.name] = lane
            lane += 1
    return lanes


def build_cs_graph(changesets: list[Changeset], branch_nodes: list[BranchNode]) -> list[CSGraphRow]:
    """Build one CSGraphRow per changeset for the table graph column.

    changesets must be in table display order (newest first).
    """
    if not changesets:
        return []
    lanes = assign_lanes(branch_nodes)

    # Find first and last row index per branch
    branch_span: dict[str, tuple[int, int]] = {}
    for i, cs in enumerate(changesets):
        b = cs.branch
        if b not in branch_span:
            branch_span[b] = (i, i)
        else:
            first, last = branch_span[b]
            branch_span[b] = (min(first, i), max(last, i))

    # active_at[i] = lanes active at row i
    active_at: list[set[int]] = [set() for _ in changesets]
    for branch, (first, last) in branch_span.items():
        lane = lanes.get(branch, len(lanes))
        for i in range(first, last + 1):
            active_at[i].add(lane)

    result = []
    for i, cs in enumerate(changesets):
        lane = lanes.get(cs.branch, len(lanes))
        result.append(CSGraphRow(
            cs_id=cs.cs_id,
            lane=lane,
            active_lanes=frozenset(active_at[i]),
            color_idx=lane % _N_GRAPH_COLORS,
        ))
    return result


def layout_dag(
    branches: list[BranchNode],
    changesets: list[Changeset],
    lane_width: int = 120,
    row_height: int = 30,
) -> list[DAGNode]:
    if not changesets:
        return []
    lanes = assign_lanes(branches)
    sorted_cs = sorted(changesets, key=lambda c: c.date)
    return [
        DAGNode(
            cs_id=cs.cs_id,
            branch=cs.branch,
            date=cs.date,
            x=lanes.get(cs.branch, len(lanes)) * lane_width,
            y=i * row_height,
        )
        for i, cs in enumerate(sorted_cs)
    ]
