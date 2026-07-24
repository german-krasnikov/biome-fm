"""Unit tests for _step() shutdown helper behaviour."""
from __future__ import annotations

import logging
from collections.abc import Callable

import pytest


def make_step(log: logging.Logger) -> Callable[[str, Callable[[], object]], None]:
    """Replicate the _step closure from _on_close() for isolated testing."""
    def _step(label: str, fn: Callable[[], object]) -> None:
        try:
            fn()
        except Exception:
            log.exception("shutdown step failed: %s", label)
    return _step


def test_step_continues_after_failure() -> None:
    log = logging.getLogger("test_shutdown")
    _step = make_step(log)

    calls: list[str] = []
    _step("a", lambda: (_ for _ in ()).throw(OSError("disk full")))
    _step("b", lambda: calls.append("b"))

    assert "b" in calls


def test_step_logs_error(caplog: pytest.LogCaptureFixture) -> None:
    log = logging.getLogger("test_shutdown_log")
    _step = make_step(log)

    with caplog.at_level(logging.ERROR, logger="test_shutdown_log"):
        _step("save_session", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    assert any("save_session" in r.message for r in caplog.records)
