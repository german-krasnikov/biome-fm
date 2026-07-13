"""Pure parse functions for CLI stdout streams — no subprocess, fully testable."""
from __future__ import annotations

import json


def parse_claude_code_line(line: str) -> str | None:
    """Claude Code CLI --output-format stream-json.

    Extracts text from assistant messages:
    {"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}
    Returns None for system/result/tool_use lines.
    """
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None
    if data.get("type") != "assistant":
        return None
    content = data.get("message", {}).get("content", [])
    texts = [
        b["text"] for b in content
        if isinstance(b, dict) and b.get("type") == "text" and b.get("text")
    ]
    return "".join(texts) if texts else None


def parse_codex_line(line: str) -> str | None:
    """Codex CLI JSON lines.

    Extracts text from:
    {"role":"assistant","content":[{"type":"output_text","text":"..."}]}
    """
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None
    if data.get("role") != "assistant":
        return None
    for block in data.get("content", []):
        if isinstance(block, dict) and block.get("type") == "output_text":
            return block.get("text") or None
    return None


def parse_plain_line(line: str) -> str | None:
    """Generic plain-text fallback. Strip trailing newline; None for blank."""
    stripped = line.rstrip("\n").strip()
    return stripped if stripped else None


def _tool_label(name: str, inp: dict) -> str:
    for key in ("file_path", "path", "command", "pattern", "query"):
        if val := inp.get(key):
            s = str(val)
            return f"{name}: {s.rsplit('/', 1)[-1] if '/' in s else s[:60]}"
    return name


def parse_claude_code_events(line: str) -> list[tuple[str, str]]:
    """Parse stream-json line into list of (kind, content) events."""
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return []
    if data.get("type") != "assistant":
        return []
    events: list[tuple[str, str]] = []
    for block in data.get("message", {}).get("content", []):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and block.get("text"):
            events.append(("text", block["text"]))
        elif block.get("type") == "tool_use" and block.get("name"):
            events.append(("tool", _tool_label(block["name"], block.get("input", {}))))
    return events
