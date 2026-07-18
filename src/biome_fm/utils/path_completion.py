"""Path completion helper for command line tab-completion (F270)."""
from __future__ import annotations

import glob
from pathlib import Path


def path_completions(text: str) -> list[str]:
    """Return sorted glob matches for text if it looks like a path.

    Returns empty list for non-path text (commands, empty string, etc.).
    Supports absolute paths (/…), tilde (~…), and relative (./ …).
    """
    if not text or not any(text.startswith(p) for p in ("/", "~", "./")):
        return []
    expanded = text if not text.startswith("~") else str(Path.home()) + text[1:]
    return sorted(glob.glob(expanded + "*"))
