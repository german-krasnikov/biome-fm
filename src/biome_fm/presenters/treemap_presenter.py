"""TreemapPresenter — Qt-free directory size scanner + squarify layout."""
from __future__ import annotations

import os
import queue
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple, Protocol

_PALETTE = [
    "#D55E00", "#CC79A7", "#009E73", "#0072B2",
    "#E69F00", "#56B4E9", "#F0E442", "#000072",
]


class TreemapNode(NamedTuple):
    path: Path
    size: int
    color: str


class TreemapViewProtocol(Protocol):
    def set_nodes(self, nodes: list[TreemapNode]) -> None: ...


def squarify(
    nodes: list[TreemapNode], x: float, y: float, w: float, h: float
) -> list[tuple[TreemapNode, tuple[float, float, float, float]]]:
    """Slice-based treemap layout. Returns (node, (x, y, w, h)) per node.

    ponytail: simple horizontal/vertical slice; replace with Bruls squarify for
    better aspect ratios if visual quality matters.
    """
    if not nodes or w <= 0 or h <= 0:
        return []
    total = sum(n.size for n in nodes)
    if not total:
        return []

    result: list[tuple[TreemapNode, tuple[float, float, float, float]]] = []
    if w >= h:
        cx = x
        for i, node in enumerate(nodes):
            nw = (x + w - cx) if i == len(nodes) - 1 else w * node.size / total
            result.append((node, (cx, y, nw, h)))
            cx += nw
    else:
        cy = y
        for i, node in enumerate(nodes):
            nh = (y + h - cy) if i == len(nodes) - 1 else h * node.size / total
            result.append((node, (x, cy, w, nh)))
            cy += nh
    return result


class TreemapPresenter:
    _TIMEOUT = 5.0

    def __init__(self, view: TreemapViewProtocol) -> None:
        self._view = view
        self._queue: queue.SimpleQueue[list[TreemapNode]] = queue.SimpleQueue()
        self._cancel = threading.Event()

    def scan(self, path: Path) -> None:
        self._cancel.set()
        self._cancel = threading.Event()
        cancel = self._cancel
        q = self._queue
        timeout = self._TIMEOUT

        def _worker() -> None:
            try:
                nodes = _scan_dir(path, cancel, timeout)
            except Exception:
                nodes = []
            q.put(nodes)

        threading.Thread(target=_worker, daemon=True).start()

    def drain(self) -> None:
        try:
            nodes = self._queue.get_nowait()
            self._view.set_nodes(nodes)
        except queue.Empty:
            pass


def _scan_dir(path: Path, cancel: threading.Event, timeout: float) -> list[TreemapNode]:
    """Walk *path*, group by extension, return nodes sorted by size desc."""
    ext_sizes: dict[str, int] = defaultdict(int)
    deadline = time.monotonic() + timeout

    for dirpath, _, files in os.walk(path):
        if cancel.is_set() or time.monotonic() > deadline:
            break
        for fname in files:
            try:
                size = (Path(dirpath) / fname).stat().st_size
                ext = Path(fname).suffix.lower() or ".other"
                ext_sizes[ext] += size
            except OSError:
                pass

    items = sorted(ext_sizes.items(), key=lambda kv: kv[1], reverse=True)
    return [
        TreemapNode(path=path / ext.lstrip("."), size=sz, color=_PALETTE[i % len(_PALETTE)])
        for i, (ext, sz) in enumerate(items)
    ]
