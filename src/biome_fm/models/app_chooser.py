"""Platform-specific app discovery for 'Open With' dialog."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def discover_apps() -> list[dict]:
    """Return list of {name, command} dicts for launchable apps."""
    try:
        if sys.platform == "darwin":
            return _discover_darwin()
        if sys.platform == "win32":
            return _discover_win32()
        return _discover_xdg()
    except Exception:
        return []


def _discover_darwin() -> list[dict]:
    result = subprocess.run(
        ["mdfind", "kMDItemContentType == 'com.apple.application-bundle'"],
        capture_output=True, text=True, timeout=5,
    )
    apps = []
    for line in result.stdout.splitlines():
        p = Path(line.strip())
        if p.suffix == ".app" and p.exists():
            apps.append({"name": p.stem, "command": f"open -a {p.name!r} {{f}}"})
    return apps


def _discover_win32() -> list[dict]:
    # ponytail: stub — reads registry HKCR\.ext\OpenWithList; add per-ext filtering if needed
    return []


def _discover_xdg() -> list[dict]:
    result = subprocess.run(
        ["xdg-mime", "query", "default", "inode/directory"],
        capture_output=True, text=True, timeout=5,
    )
    desktop = result.stdout.strip()
    if desktop:
        name = desktop.replace(".desktop", "")
        return [{"name": name, "command": "xdg-open {f}"}]
    return [{"name": "xdg-open", "command": "xdg-open {f}"}]
