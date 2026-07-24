"""Unit tests for nl_ops_presenter — TDD Red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock


from biome_fm.ai.provider import NoOpProvider
from biome_fm.presenters.nl_ops_presenter import _resolve_in_cwd, parse_nl_operation


def _mock_provider(response: str) -> MagicMock:
    p = MagicMock()
    p.available = True
    p.chat.return_value = response
    return p


def test_noop_provider_returns_none() -> None:
    result = parse_nl_operation("move all .txt files to docs/", Path("/tmp"), NoOpProvider())
    assert result is None


def test_valid_json_parsed(tmp_path: Path) -> None:
    """Use tmp_path so resolve() returns a stable real path."""
    payload = json.dumps({
        "description": "Move all .txt files to docs/",
        "op": "move",
        "sources": ["a.txt", "b.txt"],
        "destination": "docs",
    })
    result = parse_nl_operation("move all .txt files to docs/", tmp_path, _mock_provider(payload))
    assert result is not None
    assert result.op == "move"
    assert result.description == "Move all .txt files to docs/"
    assert result.sources == [tmp_path / "a.txt", tmp_path / "b.txt"]
    assert result.destination == tmp_path / "docs"


def test_malformed_json_returns_none() -> None:
    result = parse_nl_operation("do something", Path("/tmp"), _mock_provider("not json at all"))
    assert result is None


def test_sources_resolved_against_cwd(tmp_path: Path) -> None:
    """Use tmp_path so resolve() returns a stable real path."""
    payload = json.dumps({"description": "x", "op": "copy", "sources": ["foo.py"], "destination": "backup"})
    result = parse_nl_operation("copy foo.py to backup", tmp_path, _mock_provider(payload))
    assert result is not None
    assert result.sources[0] == tmp_path / "foo.py"
    assert result.destination == tmp_path / "backup"


def test_missing_destination() -> None:
    cwd = Path("/tmp")
    payload = json.dumps({"description": "Delete files", "op": "delete", "sources": ["junk.txt"], "destination": None})
    result = parse_nl_operation("delete junk.txt", cwd, _mock_provider(payload))
    assert result is not None
    assert result.destination is None


# ── Security: path traversal prevention ─────────────────────────────────────

def test_parse_nl_operation_rejects_traversal(tmp_path: Path) -> None:
    resp = json.dumps({"description": "evil", "op": "delete",
                       "sources": ["../../etc/passwd"], "destination": None})
    op = parse_nl_operation("delete passwd", tmp_path, _mock_provider(resp))
    assert op is not None
    assert op.sources == []


def test_parse_nl_operation_rejects_absolute_source(tmp_path: Path) -> None:
    resp = json.dumps({"description": "evil", "op": "delete",
                       "sources": ["/etc/shadow"], "destination": None})
    op = parse_nl_operation("delete shadow", tmp_path, _mock_provider(resp))
    assert op is not None
    assert op.sources == []


def test_parse_nl_operation_rejects_absolute_destination(tmp_path: Path) -> None:
    resp = json.dumps({"description": "evil", "op": "copy",
                       "sources": ["file.txt"], "destination": "/etc/cron.d"})
    op = parse_nl_operation("copy file", tmp_path, _mock_provider(resp))
    assert op is not None
    assert op.destination is None


def test_resolve_in_cwd_accepts_nested(tmp_path: Path) -> None:
    result = _resolve_in_cwd(tmp_path, "subdir/report.pdf")
    assert result == tmp_path / "subdir" / "report.pdf"


def test_resolve_in_cwd_rejects_traversal(tmp_path: Path) -> None:
    assert _resolve_in_cwd(tmp_path, "../../etc/passwd") is None


def test_resolve_in_cwd_rejects_absolute(tmp_path: Path) -> None:
    assert _resolve_in_cwd(tmp_path, "/etc/passwd") is None


# ── Structured output validation (Item #58) ─────────────────────────────────

def test_invalid_op_returns_none(tmp_path: Path) -> None:
    """op not in VALID_OPS → None."""
    payload = json.dumps({"description": "x", "op": "rm -rf", "sources": ["a.txt"], "destination": None})
    assert parse_nl_operation("rm something", tmp_path, _mock_provider(payload)) is None


def test_empty_op_returns_none(tmp_path: Path) -> None:
    payload = json.dumps({"description": "x", "op": "", "sources": [], "destination": None})
    assert parse_nl_operation("do nothing", tmp_path, _mock_provider(payload)) is None


def test_sources_as_string_returns_none(tmp_path: Path) -> None:
    """AI hallucination: sources is a string, not a list."""
    payload = json.dumps({"description": "x", "op": "copy", "sources": "file.txt", "destination": None})
    assert parse_nl_operation("copy file.txt", tmp_path, _mock_provider(payload)) is None


def test_markdown_fence_stripped(tmp_path: Path) -> None:
    """AI wraps JSON in ```json ... ``` — must still parse."""
    inner = json.dumps({"description": "d", "op": "delete", "sources": ["x.log"], "destination": None})
    fenced = f"```json\n{inner}\n```"
    result = parse_nl_operation("delete x.log", tmp_path, _mock_provider(fenced))
    assert result is not None
    assert result.op == "delete"


def test_system_prompt_passed_to_provider(tmp_path: Path) -> None:
    """provider.chat() must be called with a non-empty system= kwarg."""
    provider = MagicMock()
    provider.available = True
    provider.chat.return_value = json.dumps(
        {"description": "d", "op": "mkdir", "sources": [], "destination": "newdir"}
    )
    parse_nl_operation("make newdir", tmp_path, provider)
    _, kwargs = provider.chat.call_args
    assert kwargs.get("system")
