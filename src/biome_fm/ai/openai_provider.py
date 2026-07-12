"""OpenAIProvider — requires `openai` package (optional dep)."""
from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar

try:
    import openai as _openai
    _HAS_OPENAI = True
except ImportError:
    _openai = None  # type: ignore
    _HAS_OPENAI = False

from biome_fm.ai.types import FileContent, ImageContent


class OpenAIProvider:
    name = "openai"
    models: ClassVar[list[str]] = ["gpt-4o", "gpt-4o-mini", "o3-mini"]

    def __init__(self, api_key: str, model: str = "gpt-4o", **_) -> None:
        if not _HAS_OPENAI:
            raise ImportError("pip install openai")
        self._client = _openai.OpenAI(api_key=api_key)
        self._model = model
        self.active_model = model

    @property
    def available(self) -> bool:
        return True

    def set_model(self, model: str) -> None:
        self._model = model
        self.active_model = model

    def chat(self, messages: list[dict], system: str = "") -> str:
        wire = self._build_wire(messages, system)
        resp = self._client.chat.completions.create(model=self._model, messages=wire)
        return resp.choices[0].message.content or ""

    def chat_stream(self, messages: list[dict], system: str = "") -> Iterator[str]:
        wire = self._build_wire(messages, system)
        stream = self._client.chat.completions.create(model=self._model, messages=wire, stream=True)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _build_wire(self, messages: list[dict], system: str) -> list[dict]:
        wire: list[dict] = []
        if system:
            wire.append({"role": "system", "content": system})
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                wire.append({"role": msg["role"], "content": content})
            elif isinstance(content, list):
                parts: list[dict] = []
                for part in content:
                    if isinstance(part, str):
                        parts.append({"type": "text", "text": part})
                    elif isinstance(part, dict):
                        parts.append(part)
                    elif isinstance(part, ImageContent):
                        parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{part.media_type};base64,{part.data}"},
                        })
                    elif isinstance(part, FileContent):
                        text = f"[{part.path.name}]\n{part.content}"
                        parts.append({"type": "text", "text": text})
                wire.append({"role": msg["role"], "content": parts})
            else:
                wire.append({"role": msg["role"], "content": str(content)})
        return wire
