"""QLocalServer-based IPC for controlling a running biome-fm instance."""
from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from biome_fm.event_bus import EventBus, IPCCommandReceived

SOCKET_NAME = "biome-fm"


class IPCServer(QObject):
    command_received = Signal(dict)

    def __init__(self, bus: EventBus, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._bus = bus
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)

    def start(self) -> bool:
        QLocalServer.removeServer(SOCKET_NAME)
        return self._server.listen(SOCKET_NAME)

    def stop(self) -> None:
        self._server.close()

    def _on_connection(self) -> None:
        sock = self._server.nextPendingConnection()
        if sock is None:
            return
        sock.waitForReadyRead(1000)
        self._read(sock)

    def _read(self, sock: QLocalSocket) -> None:
        data = bytes(sock.readAll())
        sock.close()
        try:
            payload = json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        self._bus.publish(IPCCommandReceived(payload=payload))
