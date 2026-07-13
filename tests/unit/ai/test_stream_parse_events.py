import json

from biome_fm.ai.cli.stream_parse import parse_claude_code_events


def _line(content_blocks):
    return json.dumps({"type": "assistant", "message": {"content": content_blocks}})


def test_text_block():
    result = parse_claude_code_events(_line([{"type": "text", "text": "hello"}]))
    assert result == [("text", "hello")]


def test_tool_use_block():
    result = parse_claude_code_events(
        _line([{"type": "tool_use", "name": "Read", "input": {"file_path": "/src/foo.py"}}])
    )
    assert result == [("tool", "Read: foo.py")]


def test_mixed_blocks():
    result = parse_claude_code_events(_line([
        {"type": "tool_use", "name": "Bash", "input": {"command": "ls -la"}},
        {"type": "text", "text": "Done"},
    ]))
    assert result == [("tool", "Bash: ls -la"), ("text", "Done")]


def test_system_line_returns_empty():
    assert parse_claude_code_events(json.dumps({"type": "system", "subtype": "init"})) == []


def test_blank_line_returns_empty():
    assert parse_claude_code_events("") == []


def test_tool_no_input():
    result = parse_claude_code_events(
        _line([{"type": "tool_use", "name": "ListFiles", "input": {}}])
    )
    assert result == [("tool", "ListFiles")]
