"""CliProvider — AIProviderProtocol via subprocess.Popen."""
from __future__ import annotations

import contextlib
import logging
import logging.handlers
import subprocess
import threading
from collections.abc import Iterator
from pathlib import Path

from biome_fm.ai.cli.backend_def import BackendDef

_log = logging.getLogger(__name__)

_log_dir = Path.home() / ".biome-fm"
try:
    _log_dir.mkdir(parents=True, exist_ok=True)
    _fh = logging.handlers.RotatingFileHandler(
        str(_log_dir / "ai.log"), maxBytes=1_000_000, backupCount=1,
    )
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _log.addHandler(_fh)
    _log.setLevel(logging.DEBUG)
except OSError:
    pass

_STDERR_LOG = _log_dir / "ai_stderr.log"


class CliProvider:
    """Runs a CLI tool as a subprocess, streams stdout back as tokens.

    stderr goes directly to a log file (no pipe) to avoid deadlock when
    --verbose produces heavy output.
    """

    def __init__(self, backend: BackendDef) -> None:
        self._backend = backend
        self.name = backend.name
        self.models: list[str] = list(backend.models)
        self.active_model: str = backend.models[0]
        self._available = backend.resolve_binary() is not None
        self._proc: subprocess.Popen | None = None  # type: ignore[type-arg]
        self._proc_lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self._available

    @property
    def supports_events(self) -> bool:
        return self._backend.parse_events is not None

    def set_model(self, model: str) -> None:
        self.active_model = model

    def terminate(self) -> None:
        with self._proc_lock:
            if self._proc is not None:
                self._proc.terminate()

    @contextlib.contextmanager
    def _proc_ctx(self, argv: list[str]):
        """Start subprocess, yield it, clean up on exit (even on exception)."""
        stderr_fh = None
        try:  # noqa: SIM105
            stderr_fh = open(_STDERR_LOG, "ab")  # noqa: SIM115
        except OSError:
            pass
        try:
            proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=stderr_fh or subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except (FileNotFoundError, OSError):
            if stderr_fh:
                stderr_fh.close()
            raise
        with self._proc_lock:
            self._proc = proc
        try:
            yield proc
        finally:
            with self._proc_lock:
                self._proc = None
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            if stderr_fh:
                stderr_fh.close()

    def chat(self, messages: list[dict[str, object]], system: str = "") -> str:
        return "".join(self.chat_stream(messages, system))

    def chat_stream_events(
        self, messages: list[dict[str, object]], system: str = ""
    ) -> Iterator[tuple[str, str]]:
        """Yield (kind, content) tuples — 'text' or 'tool'."""
        if self._backend.parse_events is None:
            for token in self.chat_stream(messages, system):
                yield ("text", token)
            return
        prompt = self._build_prompt(messages, system)
        argv = self._backend.build_argv(prompt, self.active_model)
        try:
            with self._proc_ctx(argv) as proc:
                yielded_any = False
                for raw in proc.stdout:  # type: ignore[union-attr]
                    for kind, content in self._backend.parse_events(
                        raw.decode("utf-8", errors="replace")
                    ):
                        yield (kind, content)
                        if kind == "text":
                            yielded_any = True
        except (FileNotFoundError, OSError) as exc:
            yield ("text", f"[Error: CLI binary not found: {exc}]")
            return
        if not yielded_any and proc.returncode != 0:
            err = _read_last_stderr()
            msg = err or f"exit code {proc.returncode}"
            yield ("text", f"[Error from {self._backend.name}]: {msg}")

    def chat_stream(self, messages: list[dict[str, object]], system: str = "") -> Iterator[str]:
        prompt = self._build_prompt(messages, system)
        argv = self._backend.build_argv(prompt, self.active_model)
        _log.info("CLI start: %s model=%s", self._backend.name, self.active_model)
        try:
            with self._proc_ctx(argv) as proc:
                yielded_any = False
                for raw in proc.stdout:  # type: ignore[union-attr]
                    token = self._backend.parse_line(raw.decode("utf-8", errors="replace"))
                    if token:
                        yield token
                        yielded_any = True
        except (FileNotFoundError, OSError) as exc:
            _log.error("CLI binary not found: %s", exc)
            yield f"[Error: CLI binary not found: {exc}]"
            return
        _log.info(
            "CLI done: %s exit=%s yielded=%s",
            self._backend.name, proc.returncode, yielded_any,
        )
        if not yielded_any and proc.returncode != 0:
            err = _read_last_stderr()
            yield f"[Error from {self._backend.name}]: {err or f'exit code {proc.returncode}'}"

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


def _read_last_stderr(max_bytes: int = 2000) -> str:
    """Read last N bytes from stderr log for error reporting."""
    try:
        data = _STDERR_LOG.read_bytes()
        return data[-max_bytes:].decode("utf-8", errors="replace").strip()
    except OSError:
        return ""
