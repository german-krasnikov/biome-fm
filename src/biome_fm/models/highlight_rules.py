"""File highlighting rules — pure Python, no Qt."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass


@dataclass(frozen=True)
class HighlightRule:
    pattern: str  # glob pattern like "*.log"
    color: str    # hex color like "#888888"


def match_highlight(name: str, rules: list[HighlightRule]) -> str | None:
    """Return color of first matching rule (case-insensitive), or None."""
    nl = name.lower()
    for rule in rules:
        if fnmatch.fnmatch(nl, rule.pattern.lower()):
            return rule.color
    return None
