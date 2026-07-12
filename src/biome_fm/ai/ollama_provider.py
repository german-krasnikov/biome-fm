"""OllamaProvider — uses httpx (available via anthropic dep) or fallback."""
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import ClassVar

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    httpx = None  # type: ignore
    _HAS_HTTPX = False

from biome_fm.ai.types import FileContent, ImageContent


class OllamaProvider:
    name = "ollama"
    models: ClassVar[list[str]] = ["llama3.2", "mistral", "gemma3"]

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.2", **_
    ) -> None:
        if not _HAS_HTTPX:
            raise ImportError("pip install httpx")
        self._base = base_url.rstrip("/")
        self._model = model
        self.active_model = model
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                httpx.get(f"{self._base}/api/tags", timeout=1.0)
                self._available = True
            except Exception:
                self._available = False
        return self._available

    def set_model(self, model: str) -> None:
        self._model = model
        self.active_model = model

    def chat(self, messages: list[dict], system: str = "") -> str:
        return "".join(self.chat_stream(messages, system))

    def chat_stream(self, messages: list[dict], system: str = "") -> Iterator[str]:
        wire = self._build_wire(messages, system)
        with httpx.stream(
            "POST", f"{self._base}/api/chat",
            json={"model": self._model, "messages": wire, "stream": True},
            timeout=120,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if token := data.get("message", {}).get("content", ""):
                    yield token
                if data.get("done"):
                    break

    def _build_wire(self, messages: list[dict], system: str) -> list[dict]:
        wire: list[dict] = []
        if system:
            wire.append({"role": "system", "content": system})
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                wire.append({"role": msg["role"], "content": content})
            elif isinstance(content, list):
                texts, images = [], []
                for part in content:
                    if isinstance(part, str):
                        texts.append(part)
                    elif isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif isinstance(part, FileContent):
                        texts.append(f"[{part.path.name}]\n{part.content}")
                    elif isinstance(part, ImageContent):
                        images.append(part.data)
                entry: dict = {"role": msg["role"], "content": "\n".join(texts)}
                if images:
                    entry["images"] = images
                wire.append(entry)
            else:
                wire.append({"role": msg["role"], "content": str(content)})
        return wire
