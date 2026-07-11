"""AIProvider protocol, NoOp default, and factory."""
from __future__ import annotations

import os
from typing import Protocol


class AIProviderProtocol(Protocol):
    @property
    def available(self) -> bool: ...
    def chat(self, messages: list[dict[str, str]], system: str = "") -> str: ...


class NoOpProvider:
    @property
    def available(self) -> bool:
        return False

    def chat(self, messages: list[dict[str, str]], system: str = "") -> str:
        return ""


def _import_claude() -> type:
    from biome_fm.ai.claude_provider import ClaudeProvider
    return ClaudeProvider


try:
    ClaudeProvider = _import_claude()
except ImportError:
    ClaudeProvider = None  # type: ignore


def make_provider(api_key: str = "") -> AIProviderProtocol:
    """Returns ClaudeProvider if key available, else NoOp."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if key and ClaudeProvider is not None:
        try:
            return ClaudeProvider(key)
        except ImportError:
            pass
    return NoOpProvider()
