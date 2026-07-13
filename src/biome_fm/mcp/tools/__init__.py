"""MCP tools package — shared helpers."""
from __future__ import annotations

from pathlib import Path


def _validate_path(p: str, allowed_roots: list[Path] | None = None) -> Path:
    """Resolve path and enforce allowed_roots. Raises PermissionError on escape."""
    resolved = Path(p).resolve()
    if allowed_roots:
        if not any(resolved.is_relative_to(root) for root in allowed_roots):
            raise PermissionError(f"Path outside allowed roots: {resolved}")
    return resolved
