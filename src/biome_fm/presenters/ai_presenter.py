"""AIPresenter — Qt-free AI chat logic."""
from __future__ import annotations

import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from biome_fm.ai.provider import AIProviderProtocol
from biome_fm.models.file_item import FileItem


class AIChatViewProtocol(Protocol):
    def append_message(self, role: str, content: str) -> None: ...
    def set_busy(self, busy: bool) -> None: ...


@dataclass
class _AIEvent:
    role: str  # "assistant" | "error"
    content: str


class AIPresenter:
    def __init__(self, view: AIChatViewProtocol, provider: AIProviderProtocol) -> None:
        self._view = view
        self._provider = provider
        self._history: list[dict[str, str]] = []
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=1)
        self._events: queue.SimpleQueue[_AIEvent] = queue.SimpleQueue()
        self._cwd: Path | None = None
        self._selected: list[FileItem] = []

    def set_context(self, cwd: Path, selected: list[FileItem]) -> None:
        self._cwd = cwd
        self._selected = selected

    def send(self, text: str) -> None:
        """Non-blocking. Response arrives via drain()."""
        if not self._provider.available:
            self._view.append_message("assistant", "(AI not configured — set ANTHROPIC_API_KEY)")
            return
        with self._lock:
            self._history.append({"role": "user", "content": text})
            snapshot = list(self._history)
        system = self._build_system()
        self._view.append_message("user", text)
        self._view.set_busy(True)
        try:
            self._pool.submit(self._run, snapshot, system)
        except RuntimeError:
            with self._lock:
                self._history.pop()
            self._view.set_busy(False)

    def suggest_rename(self, item: FileItem) -> None:
        self.send(f"Suggest 5 concise file names for: {item.name}")

    def explain_file(self, item: FileItem) -> None:
        self.send(
            f"In one sentence, what does this file likely contain?"
            f" Name: {item.name}, size: {item.size} bytes"
        )

    def drain(self) -> None:
        """Pull pending responses. Call from QTimer on main thread."""
        try:
            while True:
                ev = self._events.get_nowait()
                self._view.set_busy(False)
                if ev.role == "assistant":
                    with self._lock:
                        self._history.append({"role": "assistant", "content": ev.content})
                self._view.append_message(ev.role, ev.content)
        except queue.Empty:
            pass

    def shutdown(self) -> None:
        self._pool.shutdown(wait=True, cancel_futures=True)

    def _build_system(self) -> str:
        parts = ["You are a concise file manager assistant."]
        if self._cwd:
            parts.append(f"Current directory: {self._cwd}.")
        if self._selected:
            names = ", ".join(i.name for i in self._selected[:10])
            parts.append(f"Selected files: {names}.")
        return " ".join(parts)

    def _run(self, messages: list[dict[str, str]], system: str) -> None:
        try:
            response = self._provider.chat(messages, system)
            self._events.put(_AIEvent("assistant", response))
        except Exception as e:
            self._events.put(_AIEvent("error", str(e)))
