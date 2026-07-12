"""Unit tests for event_bus — no Qt, pure Python."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from biome_fm.event_bus import (
    ActivePaneChanged,
    EventBus,
    FilesChanged,
    OperationFinished,
    OperationStarted,
    PaneNavigated,
    SyncBrowsingToggled,
    bus,
)


@dataclass(frozen=True)
class _EventA:
    value: int


@dataclass(frozen=True)
class _EventB:
    value: str


def test_subscribe_and_publish() -> None:
    eb = EventBus()
    calls: list[_EventA] = []
    eb.subscribe(_EventA, calls.append)
    eb.publish(_EventA(1))
    assert len(calls) == 1


def test_publish_passes_event_data() -> None:
    eb = EventBus()
    received: list[_EventA] = []
    eb.subscribe(_EventA, received.append)
    evt = _EventA(42)
    eb.publish(evt)
    assert received[0] is evt


def test_unsubscribe_stops_delivery() -> None:
    eb = EventBus()
    calls: list[_EventA] = []
    eb.subscribe(_EventA, calls.append)
    eb.unsubscribe(_EventA, calls.append)
    eb.publish(_EventA(1))
    assert calls == []


def test_multiple_subscribers_all_called() -> None:
    eb = EventBus()
    a: list[_EventA] = []
    b: list[_EventA] = []
    eb.subscribe(_EventA, a.append)
    eb.subscribe(_EventA, b.append)
    eb.publish(_EventA(99))
    assert len(a) == 1 and len(b) == 1


def test_different_event_types_dont_cross() -> None:
    eb = EventBus()
    a_calls: list[_EventA] = []
    eb.subscribe(_EventA, a_calls.append)
    eb.publish(_EventB("hello"))
    assert a_calls == []


def test_publish_no_subscribers_no_crash() -> None:
    eb = EventBus()
    eb.publish(_EventA(0))  # must not raise


def test_unsubscribe_nonexistent_is_noop() -> None:
    eb = EventBus()
    eb.unsubscribe(_EventA, lambda e: None)  # must not raise


def test_concurrent_publish_thread_safe() -> None:
    eb = EventBus()
    received: list[_EventA] = []
    lock = threading.Lock()

    def handler(e: _EventA) -> None:
        with lock:
            received.append(e)

    eb.subscribe(_EventA, handler)

    threads = [threading.Thread(target=eb.publish, args=(_EventA(i),)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(received) == 10


# ── Smoke-test built-in events ────────────────────────────────────────────────

def test_files_changed_event() -> None:
    evt = FilesChanged(path=Path("/tmp"))
    assert evt.path == Path("/tmp")


def test_active_pane_changed_event() -> None:
    evt = ActivePaneChanged(pane_id="left")
    assert evt.pane_id == "left"


def test_operation_started_event() -> None:
    evt = OperationStarted(description="Copying")
    assert evt.description == "Copying"


def test_operation_finished_event() -> None:
    evt = OperationFinished(description="Done", success=True)
    assert evt.success is True
    assert evt.error == ""


def test_module_singleton_exists() -> None:
    assert isinstance(bus, EventBus)


def test_pane_navigated_event() -> None:
    eb = EventBus()
    received: list[PaneNavigated] = []
    eb.subscribe(PaneNavigated, received.append)
    evt = PaneNavigated(pane_id="left", path=Path("/home"))
    eb.publish(evt)
    assert len(received) == 1
    assert received[0].pane_id == "left"
    assert received[0].path == Path("/home")


def test_sync_browsing_toggled_event() -> None:
    eb = EventBus()
    received: list[SyncBrowsingToggled] = []
    eb.subscribe(SyncBrowsingToggled, received.append)
    eb.publish(SyncBrowsingToggled(enabled=True))
    assert received[0].enabled is True
