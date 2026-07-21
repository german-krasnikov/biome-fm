"""Macro recording and playback. Qt-free."""
from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_fm.commands.registry import CommandRegistry


class MacroRecorder:
    def __init__(self) -> None:
        self._recording: list[str] = []
        self._active: bool = False

    @property
    def is_recording(self) -> bool:
        return self._active

    def start(self) -> None:
        self._recording = []
        self._active = True

    def record(self, command_id: str) -> None:
        if self._active:
            self._recording.append(command_id)

    def stop(self) -> list[str]:
        self._active = False
        return list(self._recording)


class MacroPlayer:
    def __init__(self, registry: CommandRegistry) -> None:
        self._registry = registry

    def play(self, command_ids: list[str]) -> None:
        # ponytail: linear scan per command; fine for macro sizes (<100 steps)
        for cid in command_ids:
            entry = next((e for e in self._registry._entries if e.name == cid), None)
            if entry is not None:
                with contextlib.suppress(Exception):
                    entry.callback()
