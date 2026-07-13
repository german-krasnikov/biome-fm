from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class PanelState(Enum):
    HIDDEN = "hidden"
    OVERLAY = "overlay"
    FLOATING = "floating"


@dataclass
class Effect:
    kind: Literal["show_overlay", "show_floating", "hide", "focus_floating", "set_opposite_visible"]
    panel: str = ""
    value: bool = True  # only for set_opposite_visible


class PanelManager:
    PANELS = ("preview", "ai", "search")

    def __init__(self) -> None:
        self._states: dict[str, PanelState] = {p: PanelState.HIDDEN for p in self.PANELS}

    def state(self, name: str) -> PanelState:
        return self._states[name]

    def toggle(self, name: str) -> list[Effect]:
        cur = self._states[name]
        if cur == PanelState.HIDDEN:
            return self._transition(name, PanelState.OVERLAY)
        if cur == PanelState.OVERLAY:
            return self._transition(name, PanelState.HIDDEN)
        # FLOATING: just focus, no state change
        return [Effect("focus_floating", panel=name)]

    def detach(self, name: str) -> list[Effect]:
        if self._states[name] == PanelState.FLOATING:
            return []
        return self._transition(name, PanelState.FLOATING)

    def reattach(self, name: str) -> list[Effect]:
        if self._states[name] != PanelState.FLOATING:
            return []
        return self._transition(name, PanelState.OVERLAY)

    def on_float_closed(self, name: str) -> list[Effect]:
        if self._states[name] != PanelState.FLOATING:
            return []
        return self._transition(name, PanelState.HIDDEN)

    def set_state(self, name: str, new: PanelState) -> list[Effect]:
        """Force state transition (used by session restore)."""
        return self._transition(name, new)

    def _transition(self, name: str, new: PanelState) -> list[Effect]:
        others = [p for p in self.PANELS if p != name]
        effects: list[Effect] = []

        # Mutual exclusion: hide any other OVERLAY panels when going OVERLAY
        if new == PanelState.OVERLAY:
            for other in others:
                if self._states[other] == PanelState.OVERLAY:
                    self._states[other] = PanelState.HIDDEN
                    effects.append(Effect("hide", panel=other))

        self._states[name] = new

        if new == PanelState.HIDDEN:
            effects.append(Effect("hide", panel=name))
        elif new == PanelState.OVERLAY:
            effects.append(Effect("show_overlay", panel=name))
        else:
            effects.append(Effect("show_floating", panel=name))

        # Opposite pane visible iff no panel is OVERLAY
        any_overlay = any(s == PanelState.OVERLAY for s in self._states.values())
        effects.append(Effect("set_opposite_visible", value=not any_overlay))
        return effects
