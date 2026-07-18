"""Tests for treemap storage visualization (F330)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.presenters.treemap_presenter import TreemapNode, TreemapPresenter, squarify


@dataclass
class FakeTreemapView:
    nodes: list[TreemapNode] = field(default_factory=list)

    def set_nodes(self, nodes: list[TreemapNode]) -> None:
        self.nodes = list(nodes)


def test_treemap_node_creation():
    n = TreemapNode(path=Path("/foo"), size=100, color="#FF0000")
    assert n.path == Path("/foo")
    assert n.size == 100
    assert n.color == "#FF0000"


def test_squarify_covers_area():
    """3 nodes summing to 100 must fill a 100×100 rectangle exactly."""
    nodes = [
        TreemapNode(path=Path("a"), size=50, color="#aaa"),
        TreemapNode(path=Path("b"), size=30, color="#bbb"),
        TreemapNode(path=Path("c"), size=20, color="#ccc"),
    ]
    rects = squarify(nodes, 0.0, 0.0, 100.0, 100.0)
    assert len(rects) == 3
    total_area = sum(rw * rh for _, (_, _, rw, rh) in rects)
    assert abs(total_area - 10000.0) < 1e-6


def test_squarify_empty_returns_empty():
    assert squarify([], 0, 0, 100, 100) == []


def test_treemap_presenter_scan_builds_nodes(tmp_path):
    """Scan 3 files with distinct extensions → 3 nodes, correct sizes."""
    (tmp_path / "doc.txt").write_bytes(b"x" * 100)
    (tmp_path / "script.py").write_bytes(b"x" * 200)
    (tmp_path / "style.md").write_bytes(b"x" * 300)

    view = FakeTreemapView()
    presenter = TreemapPresenter(view)
    presenter.scan(tmp_path)

    # Poll drain until nodes arrive (max 3s)
    deadline = time.monotonic() + 3.0
    while not view.nodes and time.monotonic() < deadline:
        presenter.drain()
        time.sleep(0.05)

    assert len(view.nodes) == 3
    sizes = {n.size for n in view.nodes}
    assert sizes == {100, 200, 300}


def test_treemap_presenter_drain_noop_when_empty():
    """Calling drain() with nothing in queue must not raise."""
    view = FakeTreemapView()
    presenter = TreemapPresenter(view)
    presenter.drain()  # should not raise
    assert view.nodes == []
