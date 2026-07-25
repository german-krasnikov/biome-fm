"""Unit tests for _config — parse_config / list_config / set_config."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from biome_fm.plastic._config import list_config, parse_config, set_config


def test_parse_config_basic():
    entries = parse_config("merge.tool = plastic\nserver.name = localhost\n")
    assert any(e.key == "merge.tool" and e.value == "plastic" for e in entries)
    assert any(e.key == "server.name" and e.value == "localhost" for e in entries)


def test_parse_config_empty():
    assert parse_config("") == []


def test_parse_config_skips_blank_lines():
    entries = parse_config("\nkey = value\n\n")
    assert len(entries) == 1


def test_parse_config_skips_lines_without_equals():
    entries = parse_config("no-equals-sign\nkey = val\n")
    assert len(entries) == 1
    assert entries[0].key == "key"


def test_list_config_parses_output(tmp_path):
    out = "merge.tool = plastic\nserver.name = localhost\n"
    with patch("biome_fm.plastic._config.run_cm", return_value=out):
        entries = list_config(tmp_path)
    assert any(e.key == "merge.tool" and e.value == "plastic" for e in entries)


def test_set_config_calls_cm(tmp_path):
    with patch("biome_fm.plastic._config.run_cm") as m:
        set_config("merge.tool", "bc4", tmp_path)
    assert "set" in m.call_args[0][0]
    assert "merge.tool" in m.call_args[0][0]
    assert "bc4" in m.call_args[0][0]
