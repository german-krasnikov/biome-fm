"""Atomic write helpers shared by all store classes."""
from __future__ import annotations

import json
import logging as _logging
import tomllib as _tomllib
from pathlib import Path

from biome_fm.utils.atomic_write import atomic_write

_MISSING = object()


def atomic_write_json(path: Path, data: object, indent: int = 2) -> None:
    """Serialize data to JSON and write atomically."""
    atomic_write(path, json.dumps(data, indent=indent) + "\n")


def read_json(path: Path, default: object = _MISSING) -> object:
    """Read JSON file; return default ({} if omitted) on missing or corrupt."""
    try:
        return json.loads(path.read_text("utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if default is _MISSING else default


def safe_load_toml(path: Path, parse, default_factory):
    """Parse a TOML file with parse(data) → result. Return default_factory() on any error."""
    _log = _logging.getLogger(__name__)
    try:
        with open(path, "rb") as f:
            data = _tomllib.load(f)
        return parse(data)
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            _tomllib.TOMLDecodeError) as exc:
        _log.warning("corrupt store %s (%s) — using defaults", path, exc)
        return default_factory()


def toml_escape(s: str) -> str:
    """Escape a string for TOML double-quoted basic strings."""
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "\\r")
             .replace("\t", "\\t"))
