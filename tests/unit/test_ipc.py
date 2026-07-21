"""Unit tests for F409 IPC server/client."""
from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from biome_fm.event_bus import EventBus, IPCCommandReceived
from biome_fm.ipc.client import send_command
from biome_fm.ipc.server import IPCServer


# ── 1. server starts ──────────────────────────────────────────────────────────

def test_ipc_server_starts(qapp):
    server = IPCServer(EventBus())
    assert server.start() is True
    server.stop()


# ── 2. publish via bus ────────────────────────────────────────────────────────

def test_ipc_dispatch_publishes_event():
    bus = EventBus()
    received = []
    bus.subscribe(IPCCommandReceived, received.append)
    bus.publish(IPCCommandReceived(payload={"cmd": "cd"}))
    assert len(received) == 1
    assert received[0].payload == {"cmd": "cd"}


# ── 3. malformed JSON — no exception, no event ───────────────────────────────

def test_ipc_read_malformed_json(qapp):
    bus = EventBus()
    received = []
    bus.subscribe(IPCCommandReceived, received.append)

    server = IPCServer(bus)

    sock = MagicMock()
    sock.readAll.return_value = b"not json"

    server._read(sock)  # must not raise

    assert received == []


# ── 4. dataclass round-trip ───────────────────────────────────────────────────

def test_ipc_command_received_dataclass():
    event = IPCCommandReceived(payload={"cmd": "refresh"})
    assert event.payload == {"cmd": "refresh"}


# ── 5. client sends bytes, server receives ───────────────────────────────────

def test_send_command_connects(qapp):
    bus = EventBus()
    server = IPCServer(bus)
    assert server.start()

    received: list[IPCCommandReceived] = []
    bus.subscribe(IPCCommandReceived, received.append)

    t = threading.Thread(target=lambda: send_command({"cmd": "test"}), daemon=True)
    t.start()

    deadline = time.monotonic() + 3.0
    while not received and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.02)

    t.join(timeout=2.0)
    server.stop()

    assert received and received[0].payload == {"cmd": "test"}


# ── 6. restart after stale socket ────────────────────────────────────────────

def test_ipc_server_restart_after_stale(qapp):
    bus = EventBus()
    server = IPCServer(bus)
    assert server.start()
    server.stop()
    assert server.start() is True
    server.stop()
