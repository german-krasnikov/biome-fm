from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ViewState:
    sort_col: int = 0
    sort_asc: bool = True
    filter: str = ""
