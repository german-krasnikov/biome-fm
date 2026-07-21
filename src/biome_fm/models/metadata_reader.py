"""Read EXIF/audio metadata for rename templates. Optional deps: piexif, mutagen."""
from __future__ import annotations

from pathlib import Path

_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".tiff", ".tif"})
_AUDIO_EXTS = frozenset({".mp3", ".flac", ".ogg", ".m4a", ".aac"})


def read_metadata(path: Path) -> dict[str, str]:
    """Return flat dict of file metadata. Empty dict if unreadable or deps missing."""
    ext = path.suffix.lower()
    if ext in _IMAGE_EXTS:
        return _read_exif(path)
    if ext in _AUDIO_EXTS:
        return _read_audio(path)
    return {}


def _read_exif(path: Path) -> dict[str, str]:
    try:
        import piexif
        exif = piexif.load(str(path))
        zeroth = exif.get("0th", {})
        exif_ifd = exif.get("Exif", {})
        return {
            "make": _bytes_tag(zeroth.get(piexif.ImageIFD.Make, b"")),
            "model": _bytes_tag(zeroth.get(piexif.ImageIFD.Model, b"")),
            "date": _bytes_tag(exif_ifd.get(piexif.ExifIFD.DateTimeOriginal, b"")),
        }
    except Exception:
        return {}


def _read_audio(path: Path) -> dict[str, str]:
    try:
        from mutagen import File
        f = File(path, easy=True)
        if f is None:
            return {}
        return {
            "artist": (f.get("artist") or [""])[0],
            "title": (f.get("title") or [""])[0],
            "album": (f.get("album") or [""])[0],
            "year": (f.get("date") or [""])[0],
        }
    except Exception:
        return {}


def _bytes_tag(v) -> str:
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="ignore").strip("\x00")
    return str(v) if v else ""
