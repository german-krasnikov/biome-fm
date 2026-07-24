"""Natural language → file operation parser (pure Python, no Qt)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_VALID_OPS: frozenset[str] = frozenset({"copy", "move", "delete", "mkdir"})

_JSON_SYSTEM = (
    "You are a file operation parser. "
    "Respond ONLY with a single JSON object — no markdown, no prose, no code fences. "
    'Schema: {"description": string, "op": "copy"|"move"|"delete"|"mkdir", '
    '"sources": [string, ...], "destination": string|null}'
)


def _strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        s = s.rsplit("```", 1)[0]
    return s.strip()


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
        f"Current directory: {cwd}\n"
        f"Command: {text}\n\n"
        "Parse into the JSON schema from the system prompt."
    )

    try:
        response: str = provider.chat(  # type: ignore[union-attr]
            [{"role": "user", "content": prompt}],
            system=_JSON_SYSTEM,
        )
        data = json.loads(_strip_fences(response))
        op = data.get("op", "")
        if op not in _VALID_OPS:
            return None
        sources_raw = data.get("sources", [])
        if not isinstance(sources_raw, list):
            return None
        sources = [p for p in (_resolve_in_cwd(cwd, s) for s in sources_raw) if p is not None]
        dst_raw = data.get("destination")
        dst = _resolve_in_cwd(cwd, dst_raw) if dst_raw else None
        return NLOperation(
            description=data.get("description", text),
            op=op,
            sources=sources,
            destination=dst,
        )
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return None


def _resolve_in_cwd(cwd: Path, name: str) -> Path | None:
    """Resolve name relative to cwd; return None if it escapes cwd.

    # ponytail: resolve() hits local FS only; rework with VFS-aware path normalization
    # when NL ops extends to remote VFS
    """
    try:
        target = (cwd / name).resolve()
        if not target.is_relative_to(cwd.resolve()):
            return None
        return target
    except (ValueError, OSError):
        return None
