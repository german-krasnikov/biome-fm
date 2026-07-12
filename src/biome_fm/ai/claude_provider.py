"""ClaudeProvider — requires `anthropic` package (optional dep)."""
from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    anthropic = None  # type: ignore
    _HAS_ANTHROPIC = False

from biome_fm.ai.types import FileContent, ImageContent


class ClaudeProvider:
    name = "claude"
    models: ClassVar[list[str]] = [
        "claude-sonnet-4-20250514",
        "claude-opus-4-5-20250414",
        "claude-haiku-4-5-20251001",
    ]

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        if not _HAS_ANTHROPIC:
            raise ImportError("pip install anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self.active_model = model

    @property
    def available(self) -> bool:
        return True

    def set_model(self, model: str) -> None:
        self._model = model
        self.active_model = model

    def chat(self, messages: list[dict], system: str = "") -> str:
        wire = self._normalize_messages(messages)
        kwargs: dict = {"model": self._model, "max_tokens": 4096, "messages": wire}
        if system:
            kwargs["system"] = system
        resp = self._client.messages.create(**kwargs)
        if not resp.content:
            return "(no response)"
        return resp.content[0].text

    def chat_stream(self, messages: list[dict], system: str = "") -> Iterator[str]:
        wire = self._normalize_messages(messages)
        kwargs: dict = {"model": self._model, "max_tokens": 4096, "messages": wire}
        if system:
            kwargs["system"] = system
        with self._client.messages.stream(**kwargs) as stream:
            yield from stream.text_stream

    def _normalize_messages(self, messages: list[dict]) -> list[dict]:
        """Convert messages with ContentPart lists to Claude wire format."""
        out = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                out.append({"role": msg["role"], "content": content})
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, str):
                        parts.append({"type": "text", "text": part})
                    elif isinstance(part, dict):
                        parts.append(part)  # already wire format
                    elif isinstance(part, ImageContent):
                        parts.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": part.media_type,
                                "data": part.data,
                            },
                        })
                    elif isinstance(part, FileContent):
                        text = f"[{part.path.name}]\n{part.content}"
                        parts.append({"type": "text", "text": text})
                out.append({"role": msg["role"], "content": parts})
            else:
                out.append({"role": msg["role"], "content": str(content)})
        return out
