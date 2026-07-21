"""Session state — JSON persistence."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class TabState:
    path: str


@dataclass
class PaneSideState:
    tabs: list[TabState] = field(default_factory=lambda: [TabState(str(Path.home()))])
    active_idx: int = 0
    view_mode: str = "detail"


@dataclass
class PanelSession:
    state: str = "hidden"
    float_geometry: str = ""
    overlay_side: str = "right"


@dataclass
class SessionState:
    left: PaneSideState = field(default_factory=PaneSideState)
    right: PaneSideState = field(default_factory=PaneSideState)
    preview: PanelSession = field(default_factory=PanelSession)
    ai: PanelSession = field(default_factory=PanelSession)


def load_session(path: Path) -> SessionState | None:
    """Load session from JSON. Returns None if missing or corrupt."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        left = PaneSideState(
            tabs=[TabState(**t) for t in data["left"]["tabs"]],
            active_idx=data["left"]["active_idx"],
            view_mode=data["left"].get("view_mode", "detail"),
        )
        right = PaneSideState(
            tabs=[TabState(**t) for t in data["right"]["tabs"]],
            active_idx=data["right"]["active_idx"],
            view_mode=data["right"].get("view_mode", "detail"),
        )
        if not left.tabs or not right.tabs:
            return None
        left.active_idx = max(0, min(left.active_idx, len(left.tabs) - 1))
        right.active_idx = max(0, min(right.active_idx, len(right.tabs) - 1))
        preview = PanelSession(**data.get("preview", {})) if "preview" in data else PanelSession()
        ai = PanelSession(**data.get("ai", {})) if "ai" in data else PanelSession()
        return SessionState(left=left, right=right, preview=preview, ai=ai)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return None


def save_session(state: SessionState, path: Path) -> None:
    """Save session as JSON. Creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
