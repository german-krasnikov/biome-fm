"""Helpers for reading/writing Plastic SCM workspace config files (ignore.conf, cloaked.conf)."""
from __future__ import annotations

from pathlib import Path


def read_conf(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def write_conf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ignore_conf_path(wk_path: Path) -> Path:
    return wk_path / ".plastic" / "ignore.conf"


def cloaked_conf_path(wk_path: Path) -> Path:
    return wk_path / ".plastic" / "cloaked.conf"
