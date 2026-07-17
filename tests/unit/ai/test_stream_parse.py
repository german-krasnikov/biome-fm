"""Tests for CLI stream parsing — pure functions, no subprocess."""
import json

from biome_fm.ai.cli.stream_parse import parse_claude_code_line, parse_codex_line, parse_plain_line

# ── parse_claude_code_line ────────────────────────────────────────────────────

def test_parse_claude_code_text_block():
    line = json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": "Hello world"}]},
    })
    assert parse_claude_code_line(line) == "Hello world"


def test_parse_claude_code_system_returns_none():
    for t in ("system", "result", "tool_use"):
        line = json.dumps({"type": t, "content": "something"})
        assert parse_claude_code_line(line) is None


def test_parse_claude_code_invalid_json():
    assert parse_claude_code_line("not json at all") is None


def test_parse_claude_code_empty_content():
    line = json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "bash"}]},
    })
    assert parse_claude_code_line(line) is None


# ── parse_codex_line ──────────────────────────────────────────────────────────

def test_parse_codex_assistant_text():
    line = json.dumps({
        "role": "assistant",
        "content": [{"type": "output_text", "text": "Hi there"}],
    })
    assert parse_codex_line(line) == "Hi there"


def test_parse_codex_non_assistant_none():
    line = json.dumps({"role": "user", "content": [{"type": "output_text", "text": "x"}]})
    assert parse_codex_line(line) is None


def test_parse_codex_multi_block():
    """Multiple output_text blocks must be joined, not dropped after first."""
    line = json.dumps({
        "role": "assistant",
        "content": [
            {"type": "output_text", "text": "Hello "},
            {"type": "output_text", "text": "world"},
        ],
    })
    assert parse_codex_line(line) == "Hello world"


# ── parse_plain_line ──────────────────────────────────────────────────────────

def test_parse_plain_line_strips():
    assert parse_plain_line("hello\n") == "hello"


def test_parse_plain_line_blank_none():
    assert parse_plain_line("") is None
    assert parse_plain_line("  \n") is None
