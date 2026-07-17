"""Builtin file-extension → suggested actions mapping. No AI required."""
from __future__ import annotations

_ACTIONS: dict[str, list[tuple[str, str]]] = {
    ".py": [("Run", "run"), ("Lint", "lint")],
    ".js": [("Run with Node", "run"), ("Lint", "lint")],
    ".ts": [("Compile", "compile"), ("Lint", "lint")],
    ".jpg": [("Open Preview", "preview"), ("Convert to PNG", "convert")],
    ".jpeg": [("Open Preview", "preview"), ("Convert to PNG", "convert")],
    ".png": [("Open Preview", "preview"), ("Convert to JPG", "convert")],
    ".md": [("Preview", "preview"), ("Export HTML", "export")],
    ".json": [("Format", "format"), ("Validate", "validate")],
    ".csv": [("Open in Editor", "edit"), ("Convert to JSON", "convert")],
    ".zip": [("Extract Here", "extract")],
    ".tar": [("Extract Here", "extract")],
    ".gz": [("Extract Here", "extract")],
}


def builtin_actions(ext: str) -> list[tuple[str, str]]:
    """Return list of (label, action_id) for file extension."""
    return _ACTIONS.get(ext.lower(), [])
