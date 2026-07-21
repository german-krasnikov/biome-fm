"""Tiny HTTP→EventBus bridge for remote control. stdlib only."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from biome_fm.event_bus import EventBus, IPCCommandReceived


class _Handler(BaseHTTPRequestHandler):
    bus: EventBus
    token: str

    def do_POST(self) -> None:
        if self.token and self.headers.get("Authorization") != f"Bearer {self.token}":
            self._reply(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._reply(400, {"error": "bad json"})
            return
        self.bus.publish(IPCCommandReceived(payload=payload))
        self._reply(200, {"ok": True})

    def _reply(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_: object) -> None:
        pass


class RestAPIServer:
    def __init__(self, bus: EventBus, port: int = 0, token: str = "") -> None:
        self._bus = bus
        self._port = port
        self._token = token
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> int:
        """Start server. Returns actual port (useful when port=0 for auto-assign)."""
        handler = type("H", (_Handler,), {"bus": self._bus, "token": self._token})
        self._server = HTTPServer(("127.0.0.1", self._port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self._server.server_address[1]

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    @property
    def port(self) -> int:
        if self._server:
            return self._server.server_address[1]
        return self._port
