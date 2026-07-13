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
    texts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text" and b.get("text")]
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
