"""CliProvider — AIProviderProtocol via subprocess.Popen."""
from __future__ import annotations

import logging
import subprocess
from collections.abc import Iterator

from biome_fm.ai.cli.backend_def import BackendDef

_log = logging.getLogger(__name__)


class CliProvider:
    """Runs a CLI tool as a subprocess, streams stdout back as tokens.

    Runs on a ThreadPoolExecutor thread (called from AIPresenter._run_stream).
    generator.close() triggers finally → proc.terminate().
    """

    def __init__(self, backend: BackendDef) -> None:
        self._backend = backend
        self.name = backend.name
        self.models: list[str] = list(backend.models)
        self.active_model: str = backend.models[0]
        self._available = backend.resolve_binary() is not None

    @property
    def available(self) -> bool:
        return self._available

    def set_model(self, model: str) -> None:
        self.active_model = model

    def chat(self, messages: list[dict[str, object]], system: str = "") -> str:
        return "".join(self.chat_stream(messages, system))

    def chat_stream(self, messages: list[dict[str, object]], system: str = "") -> Iterator[str]:
        prompt = self._build_prompt(messages, system)
        argv = self._backend.build_argv(prompt, self.active_model)
        try:
            proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )
        except (FileNotFoundError, OSError) as exc:
            yield f"[Error: CLI binary not found: {exc}]"
            return
        try:
            for raw in proc.stdout:  # type: ignore[union-attr]
                token = self._backend.parse_line(raw.decode("utf-8", errors="replace"))
                if token:
                    yield token
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            if proc.stderr:
                err = proc.stderr.read().decode("utf-8", errors="replace").strip()
                if err:
                    _log.debug("CLI stderr: %s", err)

    def _build_prompt(self, messages: list[dict[str, object]], system: str) -> str:
        """Flatten message history to single string for CLI."""
        parts: list[str] = []
        if system:
            parts.append(f"System: {system}")
        for msg in messages:
            role = str(msg.get("role", "user")).capitalize()
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") if isinstance(p, dict) else str(p)
                    for p in content
                )
            parts.append(f"{role}: {content}")
        return "\n".join(parts)
