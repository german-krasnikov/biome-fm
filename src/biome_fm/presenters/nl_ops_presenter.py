"""Natural language → file operation parser (pure Python, no Qt)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class NLOperation:
    description: str
    op: str  # "copy" | "move" | "delete" | "mkdir"
    sources: list[Path] = field(default_factory=list)
    destination: Path | None = None


def parse_nl_operation(text: str, cwd: Path, provider: object) -> NLOperation | None:
    """Ask AI to parse natural language into a file operation. Returns None if unavailable."""
    if not getattr(provider, "available", False):
        return None

    prompt = (
        f"Parse this file operation command into JSON.\n"
        f"Current directory: {cwd}\n"
        f"Command: {text}\n\n"
        'Return JSON: {"description": "...", "op": "copy|move|delete|mkdir", '
        '"sources": ["filename1"], "destination": "path_or_null"}\n'
        "Only return the JSON, nothing else."
    )

    try:
        response: str = provider.chat([{"role": "user", "content": prompt}])  # type: ignore[union-attr]
        data = json.loads(response.strip())
        sources = [cwd / s for s in data.get("sources", [])]
        dst_raw = data.get("destination")
        dst = cwd / dst_raw if dst_raw else None
        return NLOperation(
            description=data.get("description", text),
            op=data.get("op", ""),
            sources=sources,
            destination=dst,
        )
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return None
