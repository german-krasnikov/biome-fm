"""Filesystem watch service. Pure Python — no Qt."""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

_log = logging.getLogger(__name__)

try:
    import watchfiles as _wf
    _WATCH_FN = _wf.watch
except ImportError:
    _WATCH_FN = None


class _Debouncer:
    """Fires callback at most once per `delay` seconds after last trigger."""

    def __init__(self, callback: Callable[[], None], delay: float) -> None:
        self._cb = callback
        self._delay = delay
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def trigger(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._delay, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        with self._lock:
            self._timer = None
        self._cb()

    def cancel(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None


class WatchService:
    """Watch a single directory; call callback(path) on changes.

    Thread-safe. Debounces rapid events via _Debouncer.
    No-op when watchfiles is not installed.
    """

    def __init__(
        self,
        callback: Callable[[Path], None],
        debounce_ms: int = 300,
        _watch_fn=None,  # injected for tests; falls back to watchfiles
    ) -> None:
        self._callback = callback
        self._debounce_s = debounce_ms / 1000.0
        self._watch_fn = _watch_fn
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self, path: Path) -> None:
        watch_fn = self._watch_fn or _WATCH_FN
        if watch_fn is None:
            return  # ponytail: silent no-op if watchfiles not installed
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run, args=(path, watch_fn), daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            t = self._thread
        if t and t.is_alive():
            t.join(timeout=2.0)

    def set_path(self, path: Path) -> None:
        self._stop.set()  # signal old thread to exit (non-blocking)
        with self._lock:
            old = self._thread
            self._thread = None
        if old and old.is_alive():
            threading.Thread(target=old.join, args=(2.0,), daemon=True).start()
        self._stop.clear()
        self.start(path)

    def _run(self, path: Path, watch_fn) -> None:
        if not path.exists():
            return
        debouncer = _Debouncer(lambda: self._callback(path), self._debounce_s)
        try:
            for _changes in watch_fn(path, stop_event=self._stop, recursive=False):
                if self._stop.is_set():
                    break
                debouncer.trigger()
        except Exception:
            _log.debug("WatchService error on %s", path, exc_info=True)
        finally:
            if self._stop.is_set():
                debouncer.cancel()  # cancelled — discard pending event
            # else: loop ended naturally — let pending timer fire
