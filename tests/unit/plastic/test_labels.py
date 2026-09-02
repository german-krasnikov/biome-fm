"""Unit tests for _labels.py — parse_labels() and get_labels()."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from biome_fm.plastic._labels import get_labels, parse_labels, create_label, delete_label, rename_label


# ── parse_labels ──────────────────────────────────────────────────────────────

def test_parse_standard_line():
    out = "v1.0|42|07/24/2026 10:00:00\n"
    result = parse_labels(out)
    assert len(result) == 1
    lbl = result[0]
    assert lbl.name == "v1.0"
    assert lbl.changeset == 42
    assert lbl.date == datetime(2026, 7, 24, 10, 0, 0)


def test_parse_multiple_labels():
    out = "v1.0|1|2026-01-01 00:00:00\nv2.0|2|2026-06-01 00:00:00\n"
    result = parse_labels(out)
    assert [l.name for l in result] == ["v1.0", "v2.0"]


def test_parse_strips_whitespace():
    out = " v1.0 | 42 | 2026-01-01 00:00:00 \n"
    lbl = parse_labels(out)[0]
    assert lbl.name == "v1.0"
    assert lbl.changeset == 42


def test_parse_skips_non_int_changeset():
    out = "v1.0|not-a-number|2026-01-01 00:00:00\n"
    assert parse_labels(out) == []


def test_parse_skips_fewer_than_three_parts():
    out = "v1.0|42\n"
    assert parse_labels(out) == []


def test_parse_empty_output():
    assert parse_labels("") == []


def test_parse_skips_blank_lines():
    out = "\nv1.0|1|2026-01-01 00:00:00\n\n"
    assert len(parse_labels(out)) == 1


# ── get_labels ────────────────────────────────────────────────────────────────

def test_get_labels_calls_run_cm_with_format(tmp_path):
    with patch("biome_fm.plastic._labels.run_cm", return_value="") as m:
        get_labels(tmp_path)
    args = m.call_args.args[0]
    assert "find" in args
    assert "labels" in args
    assert any("--format=" in a for a in args)


def test_get_labels_safe_true(tmp_path):
    with patch("biome_fm.plastic._labels.run_cm", return_value="") as m:
        get_labels(tmp_path)
    kwargs = m.call_args.kwargs
    assert kwargs.get("safe") is True


# ── create / delete / rename ──────────────────────────────────────────────────

def test_create_label_calls_run_cm(tmp_path):
    with patch("biome_fm.plastic._labels.run_cm") as m:
        create_label("v2.0", 42, tmp_path)
    m.assert_called_once_with(["label", "create", "v2.0", "cs:42"], cwd=tmp_path, timeout=None)


def test_delete_label_calls_run_cm(tmp_path):
    with patch("biome_fm.plastic._labels.run_cm") as m:
        delete_label("v1.0", tmp_path)
    m.assert_called_once_with(["label", "delete", "v1.0"], cwd=tmp_path, timeout=None)


def test_rename_label_calls_run_cm(tmp_path):
    with patch("biome_fm.plastic._labels.run_cm") as m:
        rename_label("v1.0", "v1.0-final", tmp_path)
    m.assert_called_once_with(["label", "rename", "v1.0", "v1.0-final"], cwd=tmp_path, timeout=None)


# ── C50: timeout=None for mutating label operations ───────────────────────────

def test_create_label_uses_no_timeout(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("biome_fm.plastic._labels.run_cm",
                        lambda a, **kw: calls.append(kw))
    create_label("v2.0", 42, tmp_path)
    assert "timeout" in calls[0] and calls[0]["timeout"] is None
