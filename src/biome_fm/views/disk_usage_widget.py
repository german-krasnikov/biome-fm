"""DiskUsageWidget — compact disk usage bar for the status bar."""
from __future__ import annotations

import shutil
from pathlib import Path

from biome_fm.qt import QProgressBar, QWidget


class DiskUsageWidget(QProgressBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumWidth(120)
        self.setMaximum(100)
        self.setTextVisible(False)

    def update_path(self, path: Path) -> None:
        usage = shutil.disk_usage(path)
        self.setValue(int(usage.used / usage.total * 100))
        self.setToolTip(f"{usage.free // (1024 ** 3)} GB free")
