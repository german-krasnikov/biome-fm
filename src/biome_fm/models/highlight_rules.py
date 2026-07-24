"""File highlighting rules — pure Python, no Qt."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass

HIGHLIGHT_PRESETS: dict[str, list[dict]] = {
    "default": [],
    "dark": [
        {"pattern": "*.zip,*.tar,*.gz,*.bz2,*.7z,*.rar,*.xz", "color": "#a3e7a3"},
        {"pattern": "*.sh,*.bash,*.zsh,*.fish,*.bat,*.cmd,*.exe", "color": "#7ecdf7"},
        {"pattern": "*.mp3,*.mp4,*.mkv,*.avi,*.mov,*.jpg,*.jpeg,*.png,*.gif,*.webp,*.svg", "color": "#f7a8d8"},
        {"pattern": "*.pdf,*.doc,*.docx,*.odt,*.md,*.rst,*.txt", "color": "#c4b5fd"},
        {"pattern": "*.py,*.js,*.ts,*.rs,*.go,*.c,*.cpp,*.h,*.java,*.rb,*.kt,*.swift", "color": "#fcd34d"},
        {"pattern": "*.json,*.toml,*.yaml,*.yml,*.xml,*.env,*.ini,*.cfg,*.conf", "color": "#fb923c"},
    ],
    "light": [
        {"pattern": "*.zip,*.tar,*.gz,*.bz2,*.7z,*.rar,*.xz", "color": "#166534"},
        {"pattern": "*.sh,*.bash,*.zsh,*.fish,*.bat,*.cmd,*.exe", "color": "#1e3a5f"},
        {"pattern": "*.mp3,*.mp4,*.mkv,*.avi,*.mov,*.jpg,*.jpeg,*.png,*.gif,*.webp,*.svg", "color": "#7c2d6d"},
        {"pattern": "*.pdf,*.doc,*.docx,*.odt,*.md,*.rst,*.txt", "color": "#4c1d95"},
        {"pattern": "*.py,*.js,*.ts,*.rs,*.go,*.c,*.cpp,*.h,*.java,*.rb,*.kt,*.swift", "color": "#92400e"},
        {"pattern": "*.json,*.toml,*.yaml,*.yml,*.xml,*.env,*.ini,*.cfg,*.conf", "color": "#7f3a00"},
    ],
}


@dataclass(frozen=True)
class HighlightRule:
    pattern: str  # glob pattern like "*.log"
    color: str    # hex color like "#888888"


def expand_rules(rules: list[dict]) -> list[HighlightRule]:
    """Expand comma-separated patterns into individual HighlightRule instances."""
    result = []
    for r in rules:
        for pat in r["pattern"].split(","):
            result.append(HighlightRule(pattern=pat.strip(), color=r["color"]))
    return result


def match_highlight(name: str, rules: list[HighlightRule]) -> str | None:
    """Return color of first matching rule (case-insensitive), or None."""
    nl = name.lower()
    for rule in rules:
        if fnmatch.fnmatch(nl, rule.pattern.lower()):
            return rule.color
    return None
