"""Unit tests for FileAssociations (Feature #21)."""
from __future__ import annotations

import json
from pathlib import Path

from biome_fm.models.associations import FileAssociations


def test_get_known(tmp_path: Path) -> None:
    cfg = tmp_path / "assoc.json"
    cfg.write_text(json.dumps({".py": "code", ".rs": "code"}))
    fa = FileAssociations(cfg)
    assert fa.get(".py") == "code"
    assert fa.get(".rs") == "code"


def test_unknown_returns_none(tmp_path: Path) -> None:
    cfg = tmp_path / "assoc.json"
    cfg.write_text(json.dumps({".py": "code"}))
    fa = FileAssociations(cfg)
    assert fa.get(".xyz") is None


def test_set_saves(tmp_path: Path) -> None:
    cfg = tmp_path / "assoc.json"
    fa = FileAssociations(cfg)
    fa.set(".go", "goland")
    fa.save()
    fa2 = FileAssociations(cfg)
    assert fa2.get(".go") == "goland"


def test_missing_file_starts_empty(tmp_path: Path) -> None:
    fa = FileAssociations(tmp_path / "nonexistent.json")
    assert fa.get(".py") is None
