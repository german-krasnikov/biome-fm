"""Provider registry — sorted by priority, fallback if no match."""
from __future__ import annotations

from pathlib import Path

from biome_fm.preview.provider import PreviewProvider
from biome_fm.preview.providers.fallback import FallbackProvider


class PreviewRegistry:
    def __init__(self) -> None:
        self._providers: list[PreviewProvider] = []

    def register(self, provider: PreviewProvider) -> None:
        self._providers.append(provider)
        self._providers.sort(key=lambda p: p.priority)

    def find(self, path: Path) -> PreviewProvider:
        for p in self._providers:
            if p.can_handle(path):
                return p
        return FallbackProvider()
