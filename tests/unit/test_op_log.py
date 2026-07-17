"""TDD: OpLogModel."""
from __future__ import annotations

import pytest


def test_add_entry(qapp) -> None:
    from biome_fm.views.op_log_panel import OpLogModel
    model = OpLogModel(max_entries=100)
    model.add_entry("Copy", "OK", "file.txt → /dst")
    assert model.rowCount() == 1
    assert model.data(model.index(0, 1)) == "Copy"
    assert model.data(model.index(0, 2)) == "OK"
    assert model.data(model.index(0, 3)) == "file.txt → /dst"


def test_max_entries_lru(qapp) -> None:
    from biome_fm.views.op_log_panel import OpLogModel
    model = OpLogModel(max_entries=3)
    for i in range(5):
        model.add_entry(f"op{i}", "OK", "")
    assert model.rowCount() == 3
    # oldest entries pruned — most recent is op4
    assert model.data(model.index(2, 1)) == "op4"
