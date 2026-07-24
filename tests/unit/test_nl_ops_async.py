"""Unit tests for NLOpsDialog async parse — scenarios 1-2."""
from __future__ import annotations

import queue
from pathlib import Path
from unittest.mock import MagicMock


from biome_fm.ai.provider import NoOpProvider
from biome_fm.presenters.nl_ops_presenter import NLOperation, parse_nl_operation


def test_nl_ops_parse_result_queued_not_blocking():
    """_run_parse puts result in queue without blocking."""
    provider = MagicMock()
    provider.available = True
    provider.chat.return_value = (
        '{"description":"d","op":"copy","sources":["a.txt"],"destination":"b/"}'
    )

    result_q: queue.SimpleQueue = queue.SimpleQueue()
    result = parse_nl_operation("copy a.txt to b/", Path("/tmp"), provider)
    result_q.put(result)

    assert not result_q.empty()
    item = result_q.get_nowait()
    assert isinstance(item, NLOperation)
    assert item.op == "copy"


def test_nl_ops_parse_returns_none_when_unavailable():
    result = parse_nl_operation("anything", Path("/tmp"), NoOpProvider())
    assert result is None
