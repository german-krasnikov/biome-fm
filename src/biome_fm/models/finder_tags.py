"""macOS Finder tag reader via xattr. No-op on other platforms."""
from __future__ import annotations

import json
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

    _QUARANTINE_ATTR = b"com.apple.quarantine"

    def get_finder_tags(path: Path) -> list[str]:
        try:
            raw = _getxattr(str(path), "com.apple.metadata:_kMDItemUserTags")
            tags = plistlib.loads(raw)
            return [t.split("\n")[0] for t in tags if isinstance(t, str)]
        except OSError:
            return []

    def set_finder_tags(path: Path, tags: list[str]) -> None:
        raw = plistlib.dumps(tags, fmt=plistlib.FMT_BINARY)
        path_b = str(path).encode()
        attr_b = b"com.apple.metadata:_kMDItemUserTags"
        ret = _libc.setxattr(path_b, attr_b, raw, len(raw), 0, 0)
        if ret < 0:
            raise OSError(f"setxattr failed for {path}")

    def has_quarantine_flag(path: Path) -> bool:
        try:
            _getxattr(str(path), "com.apple.quarantine")
            return True
        except OSError:
            return False

    def _setxattr(path: str, attr: str, value: bytes) -> None:
        """Thin ctypes wrapper — mockable in tests."""
        path_b = path.encode()
        attr_b = attr.encode()
        if _libc.setxattr(path_b, attr_b, value, len(value), 0, 0) < 0:
            raise OSError(f"setxattr failed for {path}")

    def remove_quarantine_flag(path: Path) -> None:
        if _libc.removexattr(str(path).encode(), _QUARANTINE_ATTR, 0) < 0:
            raise OSError(f"removexattr failed for {path}")

    _COMMENT_ATTR = "com.apple.metadata:kMDItemFinderComment"

    def get_finder_comment(path: Path) -> str:
        try:
            raw = _getxattr(str(path), _COMMENT_ATTR)
            return raw.decode("utf-8", errors="replace").rstrip("\x00")
        except OSError:
            return _get_comment_fallback(path)

    def set_finder_comment(path: Path, comment: str) -> None:
        try:
            _setxattr(str(path), _COMMENT_ATTR, comment.encode())
        except OSError:
            _set_comment_fallback(path, comment)

else:
    def get_finder_tags(path: Path) -> list[str]:
        return []

    def set_finder_tags(path: Path, tags: list[str]) -> None:
        pass

    def has_quarantine_flag(path: Path) -> bool:
        return False

    def remove_quarantine_flag(path: Path) -> None:
        pass

    def get_finder_comment(path: Path) -> str:
        return _get_comment_fallback(path)

    def set_finder_comment(path: Path, comment: str) -> None:
        _set_comment_fallback(path, comment)


def _meta_path(path: Path) -> Path:
    return path.parent / f".{path.name}.biome-meta.json"


def _get_comment_fallback(path: Path) -> str:
    mp = _meta_path(path)
    try:
        return json.loads(mp.read_text()).get("comment", "")
    except (OSError, json.JSONDecodeError):
        return ""


def _set_comment_fallback(path: Path, comment: str) -> None:
    mp = _meta_path(path)
    data: dict = {}
    try:
        data = json.loads(mp.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    data["comment"] = comment
    mp.write_text(json.dumps(data))
