"""F324 — macOS Automator Quick Action: Open in Biome FM."""
from __future__ import annotations

import sys
from pathlib import Path

_SERVICE_NAME = "Open in Biome FM.workflow"
_SERVICES_DIR = Path.home() / "Library" / "Services"

_SCRIPT_TEMPLATE = """\
#!/bin/bash
# Automator Quick Action: Open in Biome FM
# Install with: biome-fm install-service
for f in "$@"; do
    if [ -d "$f" ]; then
        biome-fm "$f" &
    else
        biome-fm "$(dirname "$f")" &
    fi
done
"""


def generate_quick_action() -> str:
    """Return shell script content for the Biome FM Automator Quick Action."""
    return _SCRIPT_TEMPLATE


def install_quick_action() -> None:
    """Install the Quick Action to ~/Library/Services/ (macOS only, no-op elsewhere)."""
    if sys.platform != "darwin":
        return
    _SERVICES_DIR.mkdir(parents=True, exist_ok=True)
    dest = _SERVICES_DIR / "Open in Biome FM.sh"
    dest.write_text(generate_quick_action())
    dest.chmod(0o755)
    print(f"Installed: {dest}")
