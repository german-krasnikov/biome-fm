"""Unit tests for _partial — partial workspace operations."""
from __future__ import annotations

from unittest.mock import patch


from biome_fm.plastic._partial import (
    add_partial,
    configure_partial,
    get_partial_status,
    remove_partial,
)


def test_get_partial_status_calls_cm(tmp_path):
    with patch("biome_fm.plastic._partial.run_cm", return_value="partial status ok") as m:
        result = get_partial_status(tmp_path)
    assert result == "partial status ok"
    assert "status" in m.call_args[0][0]


def test_configure_partial_calls_cm(tmp_path):
    with patch("biome_fm.plastic._partial.run_cm", return_value="configured") as m:
        result = configure_partial(tmp_path)
    assert result == "configured"
    assert "configure" in m.call_args[0][0]


def test_add_partial_calls_cm(tmp_path):
    with patch("biome_fm.plastic._partial.run_cm") as m:
        add_partial("/src/module", tmp_path)
    assert "add" in m.call_args[0][0]
    assert "/src/module" in m.call_args[0][0]


def test_remove_partial_calls_cm(tmp_path):
    with patch("biome_fm.plastic._partial.run_cm") as m:
        remove_partial("/src/module", tmp_path)
    assert "remove" in m.call_args[0][0]
    assert "/src/module" in m.call_args[0][0]
