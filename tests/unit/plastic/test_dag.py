"""Unit tests for _dag.py — pure Python DAG layout (TDD RED phase)."""
from __future__ import annotations

from datetime import datetime

from biome_fm.plastic._dag import BranchNode, assign_lanes, layout_dag, parse_branch_dag
from biome_fm.plastic._models import Changeset


def test_parse_branch_dag_empty():
    assert parse_branch_dag("") == []


def test_parse_branch_dag_whitespace_only():
    assert parse_branch_dag("   \n\n   ") == []


def test_parse_branch_dag_line():
    result = parse_branch_dag("/main||2026-07-25|alice\n/feature|/main|2026-07-25|bob\n")
    assert len(result) == 2
    assert result[0].name == "/main"
    assert result[1].parent == "/main"


def test_parse_branch_dag_no_parent():
    result = parse_branch_dag("/main|\n")
    assert result[0].name == "/main"
    assert result[0].parent == ""


def test_assign_lanes_linear():
    branches = [BranchNode("/main", ""), BranchNode("/feature", "/main")]
    lanes = assign_lanes(branches)
    assert lanes["/main"] == 0
    assert lanes["/feature"] == 1


def test_assign_lanes_diamond():
    branches = [BranchNode("/main", ""), BranchNode("/a", "/main"), BranchNode("/b", "/main")]
    lanes = assign_lanes(branches)
    assert lanes["/a"] != lanes["/b"]


def test_assign_lanes_all_unique():
    branches = [BranchNode("/main", ""), BranchNode("/a", "/main"), BranchNode("/b", "/main")]
    lanes = assign_lanes(branches)
    assert len(set(lanes.values())) == 3


def test_layout_dag_ordering():
    branches = [BranchNode("/main", "")]
    dt1 = datetime(2026, 1, 1)
    dt2 = datetime(2026, 1, 2)
    css = [Changeset(2, dt2, "bob", "/main", "later"), Changeset(1, dt1, "alice", "/main", "first")]
    nodes = layout_dag(branches, css)
    assert nodes[0].cs_id == 1  # earlier date first
    assert nodes[0].y < nodes[1].y


def test_layout_dag_empty():
    assert layout_dag([], []) == []


def test_layout_dag_lane_x_offset():
    branches = [BranchNode("/main", ""), BranchNode("/dev", "/main")]
    dt = datetime(2026, 1, 1)
    css = [
        Changeset(1, dt, "alice", "/main", "m"),
        Changeset(2, dt, "bob", "/dev", "d"),
    ]
    nodes = layout_dag(branches, css, lane_width=100)
    main_node = next(n for n in nodes if n.branch == "/main")
    dev_node = next(n for n in nodes if n.branch == "/dev")
    assert main_node.x != dev_node.x
