"""AIProvider protocol, NoOp default, and factories."""
from __future__ import annotations

import os
from collections.abc import Iterator
from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class AIProviderProtocol(Protocol):
    name: str
    models: list[str]
    active_model: str

    @property
    def available(self) -> bool: ...
    def chat(self, messages: list[dict], system: str = "") -> str: ...
    def chat_stream(self, messages: list[dict], system: str = "") -> Iterator[str]: ...
    def set_model(self, model: str) -> None: ...


class NoOpProvider:
    name = "none"
    models: ClassVar[list[str]] = []
    active_model = ""

    @property
    def available(self) -> bool:
        return False

    def chat(self, messages: list[dict], system: str = "") -> str:
        return ""

    def chat_stream(self, messages: list[dict], system: str = "") -> Iterator[str]:
        return iter([])

    def set_model(self, model: str) -> None:
        pass


def _import_claude() -> type:
    from biome_fm.ai.claude_provider import ClaudeProvider
    return ClaudeProvider


try:
    ClaudeProvider = _import_claude()
except ImportError:
    ClaudeProvider = None  # type: ignore


def make_providers(cfg) -> dict[str, AIProviderProtocol]:
    """Build dict of available providers from Config."""
    result: dict[str, AIProviderProtocol] = {}
    # Claude
    claude_key = cfg.ai_claude_key or cfg.ai_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if claude_key:
        try:
            from biome_fm.ai.claude_provider import ClaudeProvider as _Claude
            result["claude"] = _Claude(claude_key, model=cfg.ai_claude_model)
        except ImportError:
            pass
    # OpenAI
    openai_key = cfg.ai_openai_key or os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            from biome_fm.ai.openai_provider import OpenAIProvider
            result["openai"] = OpenAIProvider(openai_key, model=cfg.ai_openai_model)
        except ImportError:
            pass
    # Ollama (no key needed)
    try:
        from biome_fm.ai.ollama_provider import OllamaProvider
        result["ollama"] = OllamaProvider(base_url=cfg.ai_ollama_url, model=cfg.ai_ollama_model)
    except ImportError:
        pass
    if not result:
        result["none"] = NoOpProvider()
    return result


def make_provider(api_key: str = "") -> AIProviderProtocol:
    """Legacy factory — returns ClaudeProvider or NoOp."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if key and ClaudeProvider is not None:
        try:
            return ClaudeProvider(key)
        except ImportError:
            pass
    return NoOpProvider()
