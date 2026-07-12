"""Platform-specific utilities."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_fm.models.file_item import FileItem

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")


def get_modifier_name() -> str:
    return "Cmd" if IS_MAC else "Ctrl"


def quick_look(path: Path) -> None:
    """Open file with platform Quick Look / preview."""
    if IS_MAC:
        subprocess.Popen(["qlmanage", "-p", str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif IS_LINUX:
        subprocess.Popen(["xdg-open", str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif IS_WIN:
        import os
        os.startfile(str(path))  # type: ignore[attr-defined]


def quick_look_item(item: FileItem | None) -> None:
    """Call quick_look only if item is real (not None, not '..')."""
    if item is not None and item.name != "..":
        quick_look(item.path)


def reveal_in_finder(path: Path) -> None:
    """Reveal path in platform file manager."""
    if IS_MAC:
        subprocess.Popen(["open", "-R", str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif IS_WIN:
        subprocess.Popen(["explorer", f"/select,{path}"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", str(path.parent)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
