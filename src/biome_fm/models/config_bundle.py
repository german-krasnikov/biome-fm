"""Config import/export as TOML bundle."""
from __future__ import annotations

import tomllib
from dataclasses import fields
from pathlib import Path

from biome_fm.config import Config, save_config


def export_config(config: Config, dest: Path) -> None:
    """Write config to dest as TOML."""
    save_config(config, dest)


def import_config(src: Path) -> dict:
    """Read TOML from src, validate keys, return dict.

    Raises ValueError on parse error.
    """
    try:
        data = tomllib.loads(src.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML: {e}") from e
    valid = {f.name for f in fields(Config)}
    return {k: v for k, v in data.items() if k in valid}
