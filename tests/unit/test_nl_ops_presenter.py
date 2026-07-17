"""Unit tests for nl_ops_presenter — TDD Red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.ai.provider import NoOpProvider
from biome_fm.presenters.nl_ops_presenter import NLOperation, parse_nl_operation


def _mock_provider(response: str) -> MagicMock:
    p = MagicMock()
    p.available = True
    p.chat.return_value = response
    return p


def test_noop_provider_returns_none() -> None:
    result = parse_nl_operation("move all .txt files to docs/", Path("/tmp"), NoOpProvider())
    assert result is None


def test_valid_json_parsed() -> None:
    payload = json.dumps({
        "description": "Move all .txt files to docs/",
        "op": "move",
        "sources": ["a.txt", "b.txt"],
        "destination": "docs",
    })
    cwd = Path("/home/user")
    result = parse_nl_operation("move all .txt files to docs/", cwd, _mock_provider(payload))
    assert result is not None
    assert result.op == "move"
    assert result.description == "Move all .txt files to docs/"
    assert result.sources == [cwd / "a.txt", cwd / "b.txt"]
    assert result.destination == cwd / "docs"


def test_malformed_json_returns_none() -> None:
    result = parse_nl_operation("do something", Path("/tmp"), _mock_provider("not json at all"))
    assert result is None


def test_sources_resolved_against_cwd() -> None:
    cwd = Path("/projects/myapp")
    payload = json.dumps({"description": "x", "op": "copy", "sources": ["foo.py"], "destination": "backup"})
    result = parse_nl_operation("copy foo.py to backup", cwd, _mock_provider(payload))
    assert result is not None
    assert result.sources[0] == Path("/projects/myapp/foo.py")
    assert result.destination == Path("/projects/myapp/backup")


def test_missing_destination() -> None:
    cwd = Path("/tmp")
    payload = json.dumps({"description": "Delete files", "op": "delete", "sources": ["junk.txt"], "destination": None})
    result = parse_nl_operation("delete junk.txt", cwd, _mock_provider(payload))
    assert result is not None
    assert result.destination is None
