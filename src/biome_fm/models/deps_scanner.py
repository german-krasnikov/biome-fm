"""Scan for cleanable dependency/build artifact directories."""
from __future__ import annotations

import os
import threading
from pathlib import Path

_DEFAULT_PATTERNS = frozenset({
    "node_modules", "__pycache__", ".venv", "venv", ".tox",
    "target", "dist", "build", ".mypy_cache", ".pytest_cache",
    ".gradle", ".cargo",
})

# Keep old name as alias so existing callers don't break
_CLEANUP_DIRS = _DEFAULT_PATTERNS


def load_junk_patterns(config_path: Path | None = None) -> frozenset[str]:
    """Load patterns from TOML [junk] patterns = [...], fall back to defaults."""
    if config_path is None or not config_path.exists():
        return _DEFAULT_PATTERNS
    import tomllib
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    raw = data.get("junk", {}).get("patterns", [])
    return frozenset(raw) if raw else _DEFAULT_PATTERNS


def scan_cleanup_dirs(
    root: Path,
    cancel: threading.Event,
    max_depth: int = 6,
    patterns: frozenset[str] | None = None,
) -> list[Path]:
    """Walk root, collect dirs matching patterns. Qt-free."""
    _patterns = patterns if patterns is not None else _DEFAULT_PATTERNS
    results: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        if cancel.is_set():
            break
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth >= max_depth:
            dirnames.clear()
            continue
        for d in list(dirnames):
            if d in _patterns:
                results.append(Path(dirpath) / d)
                dirnames.remove(d)
    return results
