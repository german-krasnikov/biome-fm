"""Unit tests for F451 — selection export path formatting (no Qt)."""
from pathlib import Path


def _export_paths(paths):
    return "\n".join(str(p) for p in paths)


def test_export_paths_to_text():
    paths = [Path("/tmp/a.txt"), Path("/tmp/b.txt")]
    assert _export_paths(paths) == "/tmp/a.txt\n/tmp/b.txt"


def test_empty_selection_exports_empty():
    assert _export_paths([]) == ""
