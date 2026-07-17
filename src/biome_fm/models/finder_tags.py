"""macOS Finder tag reader via xattr. No-op on other platforms."""
from __future__ import annotations

import sys
from pathlib import Path

_FINDER_COLORS: dict[str, str] = {
    "Red": "#ff6b6b", "Orange": "#ffa94d", "Yellow": "#ffd43b",
    "Green": "#51cf66", "Blue": "#339af0", "Purple": "#cc5de8",
    "Gray": "#adb5bd",
}


def finder_tag_color(tag_name: str) -> str | None:
    return _FINDER_COLORS.get(tag_name)


if sys.platform == "darwin":
    import ctypes
    import ctypes.util
    import plistlib

    _libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

    def _getxattr(path: str, attr: str) -> bytes:
        """Thin ctypes wrapper — mockable in tests."""
        path_b = path.encode()
        attr_b = attr.encode()
        size = _libc.getxattr(path_b, attr_b, None, 0, 0, 0)
        if size < 0:
            raise OSError(f"getxattr failed for {path}")
        buf = ctypes.create_string_buffer(size)
        if _libc.getxattr(path_b, attr_b, buf, size, 0, 0) < 0:
            raise OSError(f"getxattr failed for {path}")
        return bytes(buf)

    def get_finder_tags(path: Path) -> list[str]:
        try:
            raw = _getxattr(str(path), "com.apple.metadata:_kMDItemUserTags")
            tags = plistlib.loads(raw)
            return [t.split("\n")[0] for t in tags if isinstance(t, str)]
        except OSError:
            return []
else:
    def get_finder_tags(path: Path) -> list[str]:
        return []
