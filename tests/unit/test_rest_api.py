"""Unit tests for RestAPIServer — no Qt dependency."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

import pytest

from biome_fm.event_bus import EventBus, IPCCommandReceived
from biome_fm.ipc.rest_server import RestAPIServer


def _post(port: int, body: bytes, content_type: str = "application/json", headers: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/",
        data=body,
        method="POST",
        headers={"Content-Type": content_type, **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_rest_server_starts():
    bus = EventBus()
    srv = RestAPIServer(bus, port=0)
    port = srv.start()
    assert port > 0
    srv.stop()


def test_post_valid_json():
    bus = EventBus()
    received: list[IPCCommandReceived] = []
    bus.subscribe(IPCCommandReceived, received.append)

    srv = RestAPIServer(bus, port=0)
    port = srv.start()
    try:
        status, body = _post(port, json.dumps({"cmd": "test"}).encode())
        assert status == 200
        assert body == {"ok": True}
        # give the handler thread a moment to publish
        time.sleep(0.05)
        assert len(received) == 1
        assert received[0].payload == {"cmd": "test"}
    finally:
        srv.stop()


def test_post_bad_json():
    bus = EventBus()
    srv = RestAPIServer(bus, port=0)
    port = srv.start()
    try:
        status, body = _post(port, b"not json")
        assert status == 400
        assert body == {"error": "bad json"}
    finally:
        srv.stop()


def test_auth_required_no_token():
    bus = EventBus()
    srv = RestAPIServer(bus, port=0, token="secret")
    port = srv.start()
    try:
        status, body = _post(port, json.dumps({"cmd": "x"}).encode())
        assert status == 401
        assert body == {"error": "unauthorized"}
    finally:
        srv.stop()


def test_auth_required_correct_token():
    bus = EventBus()
    srv = RestAPIServer(bus, port=0, token="secret")
    port = srv.start()
    try:
        status, body = _post(
            port,
            json.dumps({"cmd": "x"}).encode(),
            headers={"Authorization": "Bearer secret"},
        )
        assert status == 200
        assert body == {"ok": True}
    finally:
        srv.stop()


def test_stop_server():
    bus = EventBus()
    srv = RestAPIServer(bus, port=0)
    srv.start()
    srv.stop()
    assert srv._thread is not None
    srv._thread.join(timeout=2)
    assert not srv._thread.is_alive()
