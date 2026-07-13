"""AIPresenter — Qt-free AI chat logic with streaming, attachments, multi-provider."""
from __future__ import annotations

import base64
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from biome_fm.ai.provider import AIProviderProtocol
from biome_fm.models.file_item import FileItem

MAX_FILE_BYTES = 100_000
MAX_ATTACHMENTS = 10
_IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})
_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}


class AIChatViewProtocol(Protocol):
    def append_message(self, role: str, content: str) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def append_token(self, token: str) -> None: ...
    def finalize_stream(self) -> None: ...
    def discard_stream(self) -> None: ...
    def add_attachment_chip(self, name: str) -> None: ...
    def clear_attachment_chips(self) -> None: ...
    def set_provider_list(self, providers: list[str], active: str,
                          models: list[str], active_model: str) -> None: ...
    def append_tool_event(self, description: str) -> None: ...


@dataclass
class Attachment:
    path: Path
    kind: Literal["text", "image", "folder"]
    content: str | bytes
    truncated: bool = False
    error: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.path.name}{' (truncated)' if self.truncated else ''}"


@dataclass
class _AIEvent:
    kind: Literal["token", "done", "error", "attachment_ready", "tool_call", "cancelled"]
    content: str = ""
    attachment: Attachment | None = None
    epoch: int = 0


class AIPresenter:
    def __init__(self, view: AIChatViewProtocol, providers: dict[str, AIProviderProtocol],
                 default_provider: str = "claude") -> None:
        self._view = view
        self._providers = providers
        fallback = next(iter(providers), "")
        self._active_key = default_provider if default_provider in providers else fallback
        self._history: list[dict] = []
        self._pending_attachments: list[Attachment] = []
        self._stream_buffer: list[str] = []
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=2)
        self._events: queue.SimpleQueue[_AIEvent] = queue.SimpleQueue()
        self._epoch: int = 0
        self._cwd: Path | None = None
        self._selected: list[FileItem] = []

    @property
    def _provider(self) -> AIProviderProtocol:
        from biome_fm.ai.provider import NoOpProvider
        return self._providers.get(self._active_key) or NoOpProvider()

    def switch_provider(self, name: str) -> None:
        if name in self._providers:
            self._active_key = name
            p = self._providers[name]
            self._view.set_provider_list(list(self._providers), name, p.models, p.active_model)

    def switch_model(self, model: str) -> None:
        self._provider.set_model(model)

    def set_context(self, cwd: Path, selected: list[FileItem]) -> None:
        self._cwd = cwd
        self._selected = selected

    def add_attachment(self, path: Path) -> None:
        if len(self._pending_attachments) >= MAX_ATTACHMENTS:
            return
        self._pool.submit(self._load_attachment, path)

    def remove_attachment(self, index: int) -> None:
        if 0 <= index < len(self._pending_attachments):
            self._pending_attachments.pop(index)

    def clear_attachments(self) -> None:
        self._pending_attachments.clear()
        self._view.clear_attachment_chips()

    def send(self, text: str) -> None:
        if not self._provider.available:
            self._view.append_message("assistant", "(AI not configured — set API key)")
            return
        attachments = list(self._pending_attachments)
        self._pending_attachments.clear()
        self._view.clear_attachment_chips()

        user_display = text
        if attachments:
            names = ", ".join(a.path.name for a in attachments)
            user_display = f"[{names}] {text}"

        content_blocks = self._build_content_blocks(text, attachments)
        with self._lock:
            self._history.append({"role": "user", "content": user_display})
            api_messages = [*self._history[:-1], {"role": "user", "content": content_blocks}]

        self._view.append_message("user", user_display)
        self._epoch += 1
        if hasattr(self._provider, "terminate"):
            self._provider.terminate()
        self._view.discard_stream()
        self._view.set_busy(True)
        self._stream_buffer.clear()

        system = self._build_system()
        current_epoch = self._epoch
        try:
            self._pool.submit(self._run_stream, api_messages, system, current_epoch)
        except RuntimeError:
            with self._lock:
                self._history.pop()
            self._view.set_busy(False)

    def suggest_rename(self, item: FileItem) -> None:
        self.send(f"Suggest 5 concise file names for: {item.name}")

    def explain_file(self, item: FileItem) -> None:
        self.send(f"In one sentence, what does this file likely contain?"
                  f" Name: {item.name}, size: {item.size} bytes")

    def cancel(self) -> None:
        self._epoch += 1
        self._stream_buffer.clear()
        if hasattr(self._provider, "terminate"):
            self._provider.terminate()
        self._view.discard_stream()
        self._view.set_busy(False)

    def drain(self) -> None:
        try:
            while True:
                ev = self._events.get_nowait()
                if ev.epoch != 0 and ev.epoch != self._epoch:
                    continue  # stale event from a superseded request
                if ev.kind == "token":
                    self._stream_buffer.append(ev.content)
                    self._view.append_token(ev.content)
                elif ev.kind == "done":
                    full = "".join(self._stream_buffer)
                    self._stream_buffer.clear()
                    if full:
                        with self._lock:
                            self._history.append({"role": "assistant", "content": full})
                    self._view.finalize_stream()
                    self._view.set_busy(False)
                elif ev.kind == "error":
                    self._stream_buffer.clear()
                    self._view.append_message("error", ev.content)
                    self._view.set_busy(False)
                elif ev.kind == "cancelled":
                    pass  # UI already cleaned up in cancel()
                elif ev.kind == "tool_call":
                    self._view.append_tool_event(ev.content)
                elif ev.kind == "attachment_ready" and ev.attachment:
                    self._pending_attachments.append(ev.attachment)
                    self._view.add_attachment_chip(ev.attachment.display_name)
        except queue.Empty:
            pass

    def shutdown(self) -> None:
        self._epoch += 1
        if hasattr(self._provider, "terminate"):
            self._provider.terminate()
        self._pool.shutdown(wait=True, cancel_futures=True)

    def _build_system(self) -> str:
        parts = ["You are a concise file manager assistant."]
        if self._cwd:
            parts.append(f"Current directory: {self._cwd}.")
        if self._selected:
            names = ", ".join(i.name for i in self._selected[:10])
            parts.append(f"Selected files: {names}.")
        return " ".join(parts)

    def _run_stream(self, messages: list[dict], system: str, epoch: int = 0) -> None:
        try:
            if hasattr(self._provider, "chat_stream_events"):
                for kind, content in self._provider.chat_stream_events(messages, system):
                    if self._epoch != epoch:
                        self._events.put(_AIEvent("cancelled", epoch=epoch))
                        return
                    if kind == "text":
                        self._events.put(_AIEvent("token", content, epoch=epoch))
                    else:
                        self._events.put(_AIEvent("tool_call", content, epoch=epoch))
            elif hasattr(self._provider, "chat_stream"):
                for token in self._provider.chat_stream(messages, system):
                    if self._epoch != epoch:
                        self._events.put(_AIEvent("cancelled", epoch=epoch))
                        return
                    self._events.put(_AIEvent("token", token, epoch=epoch))
            else:
                response = self._provider.chat(messages, system)
                if self._epoch != epoch:
                    self._events.put(_AIEvent("cancelled", epoch=epoch))
                    return
                self._events.put(_AIEvent("token", response, epoch=epoch))
            self._events.put(_AIEvent("done", epoch=epoch))
        except Exception as e:
            self._events.put(_AIEvent("error", str(e), epoch=epoch))

    def _load_attachment(self, path: Path) -> None:
        try:
            if path.is_dir():
                entries = sorted(path.iterdir())[:200]
                listing = "\n".join(f"{e.name}{'/' if e.is_dir() else ''}" for e in entries)
                att = Attachment(path, "folder", listing)
            elif path.suffix.lower() in _IMAGE_EXTS:
                att = Attachment(path, "image", path.read_bytes())
            else:
                raw = path.read_bytes()
                truncated = len(raw) > MAX_FILE_BYTES
                text_content = raw[:MAX_FILE_BYTES].decode("utf-8", errors="replace")
                att = Attachment(path, "text", text_content, truncated=truncated)
        except OSError as e:
            att = Attachment(path, "text", "", error=str(e))
        self._events.put(_AIEvent("attachment_ready", attachment=att))

    def _build_content_blocks(self, text: str, attachments: list[Attachment]) -> list[dict]:
        blocks: list[dict] = []
        for att in attachments:
            if att.error:
                msg = f"[Could not load {att.path.name}: {att.error}]"
                blocks.append({"type": "text", "text": msg})
            elif att.kind == "image" and isinstance(att.content, bytes):
                mime = _MIME.get(att.path.suffix.lower(), "image/png")
                blocks.append({"type": "image", "source": {
                    "type": "base64", "media_type": mime,
                    "data": base64.b64encode(att.content).decode(),
                }})
            else:
                label = f"=== {att.path.name} ===\n"
                if att.truncated:
                    label += "[truncated at 100 KB]\n"
                blocks.append({"type": "text", "text": label + str(att.content)})
        blocks.append({"type": "text", "text": text})
        return blocks
