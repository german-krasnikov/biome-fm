"""Unit tests for _triggers — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._triggers import (
    create_trigger,
    delete_trigger,
    list_triggers,
    parse_triggers,
)


def test_parse_triggers_basic():
    out = "1|on-checkin|after-checkin|*.py|/scripts/hook.sh\n"
    items = parse_triggers(out)
    assert len(items) == 1
    assert items[0].trigger_id == "1"
    assert items[0].name == "on-checkin"
    assert items[0].event == "after-checkin"
    assert items[0].filter == "*.py"
    assert items[0].command == "/scripts/hook.sh"


def test_parse_triggers_multiple():
    out = "1|t1|after-checkin|*|/a.sh\n2|t2|before-checkin|*.py|/b.sh\n"
    items = parse_triggers(out)
    assert len(items) == 2
    assert items[1].name == "t2"


def test_parse_triggers_pipe_in_command():
    out = "1|hook|after-checkin|*|echo foo | tee /tmp/log\n"
    items = parse_triggers(out)
    assert items[0].command == "echo foo | tee /tmp/log"


def test_parse_triggers_empty():
    assert parse_triggers("") == []
    assert parse_triggers("   \n  ") == []


def test_list_triggers_parses_output(tmp_path):
    out = "1|on-checkin|after-checkin|*.py|/scripts/hook.sh\n"
    with patch("biome_fm.plastic._triggers.run_cm", return_value=out):
        items = list_triggers(tmp_path)
    assert items[0].name == "on-checkin"
    assert items[0].trigger_id == "1"


def test_create_trigger_calls_cm(tmp_path):
    with patch("biome_fm.plastic._triggers.run_cm") as m:
        create_trigger("my-trigger", "after-checkin", "*.py", "/hook.sh", tmp_path)
    args = m.call_args[0][0]
    assert "trigger" in args
    assert "create" in args


def test_delete_trigger_calls_cm(tmp_path):
    with patch("biome_fm.plastic._triggers.run_cm") as m:
        delete_trigger("1", tmp_path)
    args = m.call_args[0][0]
    assert "trigger" in args
    assert "delete" in args
    assert "1" in args
