"""TDD tests for CSGraphRow + build_cs_graph() in _dag.py."""
from __future__ import annotations

from datetime import datetime

from biome_fm.plastic._dag import BranchNode, CSGraphRow, build_cs_graph
from biome_fm.plastic._models import Changeset

_N_COLORS = 8  # len(_GRAPH_COLORS) in _components.py


def _cs(cs_id: int, branch: str) -> Changeset:
    return Changeset(cs_id, datetime(2026, 1, 1, cs_id), "u", branch, "msg")


def test_empty_input():
    assert build_cs_graph([], []) == []


def test_single_branch_all_same_lane():
    cs = [_cs(1, "/main"), _cs(2, "/main"), _cs(3, "/main")]
    rows = build_cs_graph(cs, [BranchNode("/main", "")])
    assert all(r.lane == 0 for r in rows)
    assert all(0 in r.active_lanes for r in rows)


def test_two_branches_different_lanes():
    cs = [_cs(1, "/main"), _cs(2, "/feat"), _cs(3, "/main")]
    nodes = [BranchNode("/main", ""), BranchNode("/feat", "/main")]
    rows = build_cs_graph(cs, nodes)
    lanes = {r.cs_id: r.lane for r in rows}
    assert lanes[1] != lanes[2]  # /main vs /feat on different lanes


def test_active_lanes_span():
    # Row order: /main, /feat, /feat, /main — /feat active only at indices 1-2
    cs = [_cs(1, "/main"), _cs(2, "/feat"), _cs(3, "/feat"), _cs(4, "/main")]
    nodes = [BranchNode("/main", ""), BranchNode("/feat", "/main")]
    rows = build_cs_graph(cs, nodes)
    feat_lane = rows[1].lane  # cs_id=2 is on /feat
    assert feat_lane not in rows[0].active_lanes  # row 0: /feat not yet started
    assert feat_lane in rows[1].active_lanes
    assert feat_lane in rows[2].active_lanes
    assert feat_lane not in rows[3].active_lanes  # row 3: /feat already ended


def test_color_idx_wraps():
    branches = [BranchNode(f"/b{i}", "") for i in range(_N_COLORS + 1)]
    cs = [_cs(i + 1, f"/b{i}") for i in range(_N_COLORS + 1)]
    rows = build_cs_graph(cs, branches)
    assert all(r.color_idx == r.lane % _N_COLORS for r in rows)


def test_returns_csGraphRow_type():
    rows = build_cs_graph([_cs(1, "/main")], [BranchNode("/main", "")])
    assert isinstance(rows[0], CSGraphRow)
    assert rows[0].cs_id == 1
