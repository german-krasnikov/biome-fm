"""Generate presigned/shareable URLs for remote files. Qt-free."""
from __future__ import annotations

import subprocess
from pathlib import Path


def sign_url(path: Path, vfs: object, expiration: int = 3600) -> str | None:
    """Return presigned URL string, or None if unsupported."""
    fs = getattr(vfs, "_fs", None)
    if fs is not None and hasattr(fs, "sign"):
        try:
            return fs.sign(str(path), expiration=expiration)
        except Exception:
            return None
    if type(vfs).__name__ == "RcloneVFS":
        try:
            remote = getattr(vfs, "_remote", "")
            out = subprocess.run(
                ["rclone", "link", f"{remote}{path}"],
                capture_output=True, text=True, timeout=15,
            )
            url = out.stdout.strip()
            return url if url.startswith("http") else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
    return None
