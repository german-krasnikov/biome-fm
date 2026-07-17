"""Shared types for biome-fm plugin API."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict


class ThemeTokens(TypedDict, total=False):
    base: str       # main window background
    surface: str    # panels, inputs, table rows
    surface2: str   # alternate rows, hover, pressed
    border: str     # separators, outlines
    text: str       # primary text
    text_dim: str   # secondary text, headers, placeholders
    accent: str     # selection, focus, active borders, links
    accent2: str    # pressed state, secondary accent
    red: str        # destructive actions, errors
    green: str      # success, new files
    base_bg: str        # alias for base used by glass theme
    surface_opaque: str  # fully-opaque surface (glass: QMenu stays solid)
    surface2_opaque: str # fully-opaque surface2
    selection_bg: str   # selection background (defaults to accent)


@dataclass
class ActionSpec:
    label: str
    callback: Callable[[], None]
    shortcut: str = ""
    icon_name: str = ""        # freedesktop icon name
    separator_before: bool = False


@dataclass
class ColumnDef:
    id: str                    # unique, e.g. "git.status"
    title: str
    width: int = 80
    alignment: str = "left"    # "left" | "right" | "center"


# Inline dark fallback — safety net if TOML files missing from install
_DARK_FALLBACK: ThemeTokens = {
    "base":           "#1c1c1e",
    "base_bg":        "#1c1c1e",
    "surface":        "#2c2c2e",
    "surface_opaque": "#2c2c2e",
    "surface2":       "#3a3a3c",
    "surface2_opaque": "#3a3a3c",
    "border":         "#48484a",
    "text":           "#f5f5f7",
    "text_dim":       "#98989f",
    "accent":         "#0a84ff",
    "accent2":        "#5e5ce6",
    "red":            "#ff453a",
    "green":          "#32d74b",
    "selection_bg":   "#0a84ff",
}
