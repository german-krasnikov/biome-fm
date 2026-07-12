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
