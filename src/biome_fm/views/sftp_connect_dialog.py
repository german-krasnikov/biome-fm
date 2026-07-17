"""SFTP connection dialog."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class SFTPConnectDialog(QDialog):
    """Dialog for entering SFTP connection parameters."""

    connect_requested = Signal(str, int, str, str)  # host, port, user, password

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Connect via SFTP")
        self.setMinimumWidth(320)

        form = QFormLayout()

        self._host = QLineEdit()
        self._host.setPlaceholderText("hostname or IP")
        form.addRow("Host:", self._host)

        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(22)
        form.addRow("Port:", self._port)

        self._user = QLineEdit()
        self._user.setPlaceholderText("username")
        form.addRow("User:", self._user)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("password or leave blank for key auth")
        form.addRow("Password:", self._password)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        self.connect_requested.emit(
            self._host.text().strip(),
            self._port.value(),
            self._user.text().strip(),
            self._password.text(),
        )
        self.accept()
