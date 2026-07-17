"""Platform-aware file opener."""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path


def open_file(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    elif sys.platform == "win32":
        import os
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(path)])


def open_in_editor(path: Path, editor_cmd: str = "") -> None:
    """Open path in editor. Falls back to open_file if editor_cmd is empty."""
    if editor_cmd:
        subprocess.Popen(shlex.split(editor_cmd) + [str(path)])
    else:
        open_file(path)
