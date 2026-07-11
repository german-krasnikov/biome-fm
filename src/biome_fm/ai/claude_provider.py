"""ClaudeProvider — requires `anthropic` package (optional dep)."""
from __future__ import annotations

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    anthropic = None  # type: ignore
    _HAS_ANTHROPIC = False


class ClaudeProvider:
    @property
    def available(self) -> bool:
        return True

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        if not _HAS_ANTHROPIC:
            raise ImportError("pip install anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def chat(self, messages: list[dict[str, str]], system: str = "") -> str:
        kwargs: dict[str, object] = {"model": self._model, "max_tokens": 1024, "messages": messages}
        if system:
            kwargs["system"] = system
        resp = self._client.messages.create(**kwargs)
        if not resp.content:
            return "(no response)"
        return resp.content[0].text
